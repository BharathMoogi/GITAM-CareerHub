"""
Career Gamification Engine — Service Layer.

Manages XP calculations, Level progression, Badge awards, Challenge tracking,
Leaderboards, Career Milestones, and Reward redemption.
"""
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.gamification import (
    Level, Achievement, Badge, StudentBadge, StudentXP,
    DailyChallenge, WeeklyChallenge, MonthlyChallenge, Reward, CareerMilestone
)
from app.models.student import Student
from app.models.branch import Branch

logger = logging.getLogger("app.services.gamification")

# Action type to XP reward mapping
XP_ACTION_REWARDS = {
    "COURSE_COMPLETED": 100,
    "PROJECT_COMPLETED": 250,
    "CERTIFICATION_EARNED": 300,
    "INTERNSHIP_OFFER": 600,
    "PLACEMENT_OFFER": 1000,
}


class GamificationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── 1. XP & Level Engine ──────────────────────────────────────────────────

    async def get_student_xp(self, user_id: str) -> Dict[str, Any]:
        """Fetch student XP, level, level title, streak, and progress to next level."""
        student = await self._get_student_by_user_id(user_id)
        xp_rec = await self._get_or_create_student_xp(student.id)

        # Determine level thresholds
        levels_res = await self.db.execute(select(Level).order_by(Level.level_number))
        levels = levels_res.scalars().all()

        current_lvl_obj = next((l for l in reversed(levels) if xp_rec.total_xp >= l.min_xp), levels[0])
        next_lvl_obj = next((l for l in levels if l.level_number == current_lvl_obj.level_number + 1), None)

        if next_lvl_obj:
            xp_in_level = xp_rec.total_xp - current_lvl_obj.min_xp
            xp_needed = next_lvl_obj.min_xp - current_lvl_obj.min_xp
            progress_pct = round(min(100.0, (xp_in_level / xp_needed) * 100.0), 1)
            next_min = next_lvl_obj.min_xp
        else:
            progress_pct = 100.0
            next_min = current_lvl_obj.min_xp

        # Update if level changed
        if xp_rec.current_level != current_lvl_obj.level_number or xp_rec.level_title != current_lvl_obj.title:
            xp_rec.current_level = current_lvl_obj.level_number
            xp_rec.level_title = current_lvl_obj.title
            xp_rec.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

        return {
            "student_id": student.id,
            "total_xp": xp_rec.total_xp,
            "current_level": current_lvl_obj.level_number,
            "level_title": current_lvl_obj.title,
            "min_xp_for_current_level": current_lvl_obj.min_xp,
            "next_level_min_xp": next_min,
            "progress_percentage": progress_pct,
            "streak_days": xp_rec.streak_days,
            "last_activity_date": str(xp_rec.last_activity_date) if xp_rec.last_activity_date else None,
        }

    async def award_xp(self, student_id: str, action_type: str, custom_xp: Optional[int] = None) -> Dict[str, Any]:
        """Award XP to a student based on activity trigger."""
        xp_amount = custom_xp if custom_xp is not None else XP_ACTION_REWARDS.get(action_type, 50)
        xp_rec = await self._get_or_create_student_xp(student_id)

        old_level = xp_rec.current_level
        xp_rec.total_xp += xp_amount

        # Check streak
        today = date.today()
        if xp_rec.last_activity_date == today - timedelta(days=1):
            xp_rec.streak_days += 1
        elif xp_rec.last_activity_date != today:
            xp_rec.streak_days = 1
        xp_rec.last_activity_date = today

        # Recalculate level
        levels_res = await self.db.execute(select(Level).order_by(Level.level_number))
        levels = levels_res.scalars().all()
        new_lvl_obj = next((l for l in reversed(levels) if xp_rec.total_xp >= l.min_xp), levels[0])

        leveled_up = new_lvl_obj.level_number > old_level
        if leveled_up:
            xp_rec.current_level = new_lvl_obj.level_number
            xp_rec.level_title = new_lvl_obj.title
            # Record level up milestone
            ms = CareerMilestone(
                student_id=student_id,
                title=f"Reached Level {new_lvl_obj.level_number}: {new_lvl_obj.title}",
                description=f"Earned {xp_rec.total_xp} total XP and unlocked new career benefits!",
                category="LEVEL_UP",
            )
            self.db.add(ms)

        await self.db.commit()
        await self.db.refresh(xp_rec)

        logger.info(f"Awarded +{xp_amount} XP to student {student_id} for {action_type}. Total XP: {xp_rec.total_xp}")
        return {
            "awarded_xp": xp_amount,
            "total_xp": xp_rec.total_xp,
            "current_level": xp_rec.current_level,
            "level_title": xp_rec.level_title,
            "leveled_up": leveled_up,
        }

    # ── 2. Badges ─────────────────────────────────────────────────────────────

    async def get_badges(self, user_id: str) -> Dict[str, Any]:
        """Get student's earned badges and list of all available badges."""
        student = await self._get_student_by_user_id(user_id)

        # Earned badges
        earned_res = await self.db.execute(
            select(StudentBadge, Badge)
            .join(Badge, StudentBadge.badge_id == Badge.id)
            .where(StudentBadge.student_id == student.id)
            .order_by(desc(StudentBadge.awarded_at))
        )
        earned = []
        earned_ids = set()
        for sb, b in earned_res.all():
            earned_ids.add(b.id)
            earned.append({
                "badge_id": b.id,
                "code": b.code,
                "name": b.name,
                "description": b.description,
                "tier": b.tier,
                "category": b.category,
                "icon_url": b.icon_url,
                "awarded_at": sb.awarded_at.isoformat(),
            })

        # Available badges
        all_res = await self.db.execute(select(Badge))
        all_badges = []
        for b in all_res.scalars().all():
            all_badges.append({
                "badge_id": b.id,
                "code": b.code,
                "name": b.name,
                "description": b.description,
                "tier": b.tier,
                "category": b.category,
                "icon_url": b.icon_url,
                "is_unlocked": b.id in earned_ids,
            })

        return {
            "total_earned": len(earned),
            "earned_badges": earned,
            "all_badges": all_badges,
        }

    # ── 3. Leaderboard Engine ─────────────────────────────────────────────────

    async def get_leaderboard(
        self, scope: str = "college", branch_code: Optional[str] = None, semester: Optional[int] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Fetch leaderboard dynamically by scope:
        - college: All students across GITAM
        - department / branch: Filtered by branch_code
        - semester: Filtered by semester number
        """
        stmt = (
            select(
                Student.id,
                Student.full_name,
                Student.roll_number,
                Branch.code,
                Student.profile_photo,
                StudentXP.total_xp,
                StudentXP.current_level,
                StudentXP.level_title,
            )
            .join(Branch, Student.branch_id == Branch.id)
            .join(StudentXP, StudentXP.student_id == Student.id)
        )

        if scope in ("department", "branch") or branch_code:
            target_code = branch_code or "AIML"
            stmt = stmt.where(Branch.code == target_code)

        if semester:
            stmt = stmt.where(Student.semester == semester)

        stmt = stmt.order_by(desc(StudentXP.total_xp)).limit(limit)

        res = await self.db.execute(stmt)
        rows = res.all()

        ranks = []
        for idx, row in enumerate(rows, start=1):
            s_id, name, roll, b_code, photo, total_xp, lvl, lvl_title = row
            ranks.append({
                "student_id": s_id,
                "student_name": name,
                "roll_number": roll,
                "branch_code": b_code,
                "avatar_url": photo,
                "total_xp": total_xp,
                "current_level": lvl,
                "level_title": lvl_title,
                "rank": idx,
            })

        return {
            "scope": scope,
            "branch_code": branch_code,
            "semester": semester,
            "total_entries": len(ranks),
            "leaderboard": ranks,
        }

    # ── 4. Challenges ─────────────────────────────────────────────────────────

    async def get_challenges(self) -> Dict[str, Any]:
        """Fetch active Daily, Weekly, and Monthly challenges."""
        today = date.today()

        daily_res = await self.db.execute(
            select(DailyChallenge).where(DailyChallenge.expires_at >= today)
        )
        weekly_res = await self.db.execute(
            select(WeeklyChallenge).where(WeeklyChallenge.expires_at >= today)
        )
        monthly_res = await self.db.execute(
            select(MonthlyChallenge).where(MonthlyChallenge.expires_at >= today)
        )

        return {
            "daily_challenges": [
                {"id": c.id, "title": c.title, "description": c.description, "xp_reward": c.xp_reward, "expires_at": str(c.expires_at)}
                for c in daily_res.scalars().all()
            ],
            "weekly_challenges": [
                {"id": c.id, "title": c.title, "description": c.description, "xp_reward": c.xp_reward, "expires_at": str(c.expires_at)}
                for c in weekly_res.scalars().all()
            ],
            "monthly_challenges": [
                {"id": c.id, "title": c.title, "description": c.description, "xp_reward": c.xp_reward, "expires_at": str(c.expires_at)}
                for c in monthly_res.scalars().all()
            ],
        }

    async def claim_challenge(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Claim a challenge and award its XP reward."""
        student = await self._get_student_by_user_id(user_id)

        # Look in daily, weekly, or monthly tables
        ch = None
        for model in (DailyChallenge, WeeklyChallenge, MonthlyChallenge):
            res = await self.db.execute(select(model).where(model.id == challenge_id))
            ch = res.scalars().first()
            if ch:
                break

        if not ch:
            raise NotFoundException("Challenge not found or expired")

        result = await self.award_xp(student.id, "CHALLENGE_CLAIM", custom_xp=ch.xp_reward)
        return {
            "challenge_id": challenge_id,
            "title": ch.title,
            "xp_awarded": ch.xp_reward,
            "new_total_xp": result["total_xp"],
            "current_level": result["current_level"],
            "message": f"Successfully claimed '{ch.title}'! +{ch.xp_reward} XP added.",
        }

    # ── 5. Milestones & Rewards ───────────────────────────────────────────────

    async def get_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch career milestone timeline for a student."""
        student = await self._get_student_by_user_id(user_id)
        res = await self.db.execute(
            select(CareerMilestone)
            .where(CareerMilestone.student_id == student.id)
            .order_by(desc(CareerMilestone.achieved_at))
        )
        milestones = res.scalars().all()

        # Seed initial milestone if empty
        if not milestones:
            m = CareerMilestone(
                student_id=student.id,
                title="Joined GITAM CareerHub",
                description="Started career journey and unlocked Level 1 Explorer status",
                category="ONBOARDING",
            )
            self.db.add(m)
            await self.db.commit()
            await self.db.refresh(m)
            milestones = [m]

        return [
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "category": m.category,
                "achieved_at": m.achieved_at.isoformat(),
            }
            for m in milestones
        ]

    async def get_rewards(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch unlockable rewards and check student level eligibility."""
        student = await self._get_student_by_user_id(user_id)
        xp_rec = await self._get_or_create_student_xp(student.id)

        res = await self.db.execute(select(Reward).order_by(Reward.min_level_required))
        rewards = res.scalars().all()

        return [
            {
                "reward_id": r.id,
                "title": r.title,
                "description": r.description,
                "min_level_required": r.min_level_required,
                "xp_cost": r.xp_cost,
                "reward_type": r.reward_type,
                "is_unlocked": xp_rec.current_level >= r.min_level_required,
                "can_afford": xp_rec.total_xp >= r.xp_cost,
            }
            for r in rewards
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_student_by_user_id(self, user_id: str) -> Student:
        res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found")
        return student

    async def _get_or_create_student_xp(self, student_id: str) -> StudentXP:
        res = await self.db.execute(select(StudentXP).where(StudentXP.student_id == student_id))
        xp_rec = res.scalars().first()
        if not xp_rec:
            xp_rec = StudentXP(
                student_id=student_id,
                total_xp=100,
                current_level=1,
                level_title="Explorer",
                streak_days=1,
                last_activity_date=date.today(),
            )
            self.db.add(xp_rec)
            await self.db.commit()
            await self.db.refresh(xp_rec)
        return xp_rec
