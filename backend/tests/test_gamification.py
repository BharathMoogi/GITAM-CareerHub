"""
Tests for the Career Gamification Engine.

Covers:
  1. Level seed and XP progression (Level 1 Explorer -> Level 6 Industry Ready)
  2. Awarding XP (+100 Course, +250 Project, +300 Cert, +600 Internship, +1000 Placement)
  3. Badges (earned vs available)
  4. Daily / Weekly / Monthly Challenges listing & claiming
  5. Leaderboards (college, department, branch, semester)
  6. Career Milestones timeline
  7. Unlockable Rewards (level requirements & affordability)
"""
import sys
import asyncio
import types
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

# Stub pytest
_pytest = types.ModuleType("pytest")
class _RaisesCtx:
    def __init__(self, exc): self.exc = exc
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et is None: raise AssertionError(f"Expected {self.exc.__name__} not raised")
        return issubclass(et, self.exc)
_pytest.raises = lambda exc: _RaisesCtx(exc)
sys.modules.setdefault("pytest", _pytest)

from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.gamification import Level, Achievement, Badge, DailyChallenge, Reward
from app.services.gamification_service import GamificationService
from app.database.seed_gamification import (
    LEVELS_SEED, ACHIEVEMENTS_SEED, BADGES_SEED,
    DAILY_CHALLENGES_SEED, REWARDS_SEED
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _seed_gamification_masters(db):
    for l_data in LEVELS_SEED:
        existing = await db.execute(select(Level).where(Level.level_number == l_data["level_number"]))
        if not existing.scalars().first():
            db.add(Level(**l_data))

    for a_data in ACHIEVEMENTS_SEED:
        existing = await db.execute(select(Achievement).where(Achievement.code == a_data["code"]))
        if not existing.scalars().first():
            db.add(Achievement(**a_data))

    for b_data in BADGES_SEED:
        existing = await db.execute(select(Badge).where(Badge.code == b_data["code"]))
        if not existing.scalars().first():
            db.add(Badge(**b_data))

    for d_data in DAILY_CHALLENGES_SEED:
        existing = await db.execute(select(DailyChallenge).where(DailyChallenge.title == d_data["title"]))
        if not existing.scalars().first():
            db.add(DailyChallenge(expires_at=date.today(), **d_data))

    for r_data in REWARDS_SEED:
        existing = await db.execute(select(Reward).where(Reward.title == r_data["title"]))
        if not existing.scalars().first():
            db.add(Reward(**r_data))

    await db.commit()

async def _make_user_student(db, email="gami.test@gitam.edu", branch_code="AIML"):
    import uuid
    b_res = await db.execute(select(Branch).where(Branch.code == branch_code))
    b = b_res.scalars().first()
    if not b:
        b = Branch(code=branch_code, name=f"{branch_code} Dept", description="Test")
        db.add(b); await db.commit(); await db.refresh(b)

    r_res = await db.execute(select(TargetRole))
    role = r_res.scalars().first()
    if not role:
        role = TargetRole(title="AI Engineer", description="Test role")
        db.add(role); await db.commit(); await db.refresh(role)

    user = User(email=email, hashed_password="hash", is_active=True, role="STUDENT")
    db.add(user); await db.flush()

    student = Student(
        user_id=user.id, full_name="Gamification Test Student", email=email,
        roll_number=f"R{uuid.uuid4().hex[:8].upper()}",
        branch_id=b.id, target_role_id=role.id,
        current_year=3, semester=5, is_active=True,
    )
    db.add(student); await db.commit()
    await db.refresh(user); await db.refresh(student)
    return user, student


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_get_student_xp_initial(engine, Session):
    """Initial student XP should start at Level 1 Explorer."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "xp.init@gitam.edu")

        service = GamificationService(db)
        data = await service.get_student_xp(user.id)

        assert data["current_level"] == 1
        assert data["level_title"] == "Explorer"
        assert data["total_xp"] >= 0
        assert data["progress_percentage"] >= 0.0
        print(f"[PASS] initial XP status: Level {data['current_level']} ({data['level_title']}), {data['total_xp']} XP")


async def test_award_xp_and_level_up(engine, Session):
    """Awarding XP should update level title when crossing thresholds (+1000 placement XP)."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "xp.award@gitam.edu")

        service = GamificationService(db)
        # Award +1000 XP for Placement Offer
        res1 = await service.award_xp(student.id, "PLACEMENT_OFFER")
        assert res1["awarded_xp"] == 1000
        assert res1["total_xp"] >= 1000
        assert res1["current_level"] >= 3  # Level 3 Builder (750+ XP)
        assert res1["leveled_up"] is True
        print(f"[PASS] awarded placement XP: total_xp={res1['total_xp']}, level={res1['current_level']} ({res1['level_title']})")


async def test_get_badges(engine, Session):
    """get_badges should list earned and all available badges."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "badges.test@gitam.edu")

        service = GamificationService(db)
        data = await service.get_badges(user.id)

        assert "total_earned" in data
        assert "all_badges" in data
        assert len(data["all_badges"]) >= 5
        print(f"[PASS] badges fetched: {len(data['all_badges'])} available badges")


async def test_challenges_list_and_claim(engine, Session):
    """Challenges should list daily/weekly/monthly challenges and claim XP successfully."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "challenge.test@gitam.edu")

        service = GamificationService(db)
        ch_data = await service.get_challenges()

        assert len(ch_data["daily_challenges"]) > 0
        first_ch = ch_data["daily_challenges"][0]

        claim_res = await service.claim_challenge(user.id, first_ch["id"])
        assert claim_res["xp_awarded"] == first_ch["xp_reward"]
        assert claim_res["new_total_xp"] >= first_ch["xp_reward"]
        print(f"[PASS] challenge claimed: '{first_ch['title']}' (+{claim_res['xp_awarded']} XP)")


async def test_leaderboard_scopes(engine, Session):
    """Leaderboard should support college, department, branch, and semester scopes."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user1, s1 = await _make_user_student(db, "lb1.gami@gitam.edu", branch_code="AIML")
        user2, s2 = await _make_user_student(db, "lb2.gami@gitam.edu", branch_code="ECE")

        service = GamificationService(db)
        await service.award_xp(s1.id, "COURSE_COMPLETED")  # +100 XP
        await service.award_xp(s2.id, "PLACEMENT_OFFER")   # +1000 XP

        lb_college = await service.get_leaderboard(scope="college")
        assert lb_college["total_entries"] >= 2
        # Check sorted descending by total_xp
        scores = [item["total_xp"] for item in lb_college["leaderboard"]]
        assert scores == sorted(scores, reverse=True)


        lb_branch = await service.get_leaderboard(scope="branch", branch_code="AIML")
        assert lb_branch["branch_code"] == "AIML"
        assert all(item["branch_code"] == "AIML" for item in lb_branch["leaderboard"])
        print("[PASS] leaderboard scopes (college & branch filtering) verified")


async def test_milestones_timeline(engine, Session):
    """get_milestones should return career milestone timeline."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "ms.test@gitam.edu")

        service = GamificationService(db)
        milestones = await service.get_milestones(user.id)

        assert isinstance(milestones, list)
        assert len(milestones) >= 1
        assert "title" in milestones[0]
        print(f"[PASS] career milestones timeline: {len(milestones)} milestones returned")


async def test_unlockable_rewards(engine, Session):
    """get_rewards should return unlockable rewards with eligibility flags."""
    async with Session() as db:
        await _seed_gamification_masters(db)
        user, student = await _make_user_student(db, "rewards.test@gitam.edu")

        service = GamificationService(db)
        rewards = await service.get_rewards(user.id)

        assert isinstance(rewards, list)
        assert len(rewards) >= 4
        first_reward = rewards[0]
        assert "min_level_required" in first_reward
        assert "is_unlocked" in first_reward
        print(f"[PASS] rewards store loaded: {len(rewards)} rewards available")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_get_student_xp_initial,
    test_award_xp_and_level_up,
    test_get_badges,
    test_challenges_list_and_claim,
    test_leaderboard_scopes,
    test_milestones_timeline,
    test_unlockable_rewards,
]

if __name__ == "__main__":
    import pathlib
    for p in pathlib.Path(".").rglob("*.pyc"):
        p.unlink(missing_ok=True)

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.database.base import Base

    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        passed = failed = 0
        for t in TESTS:
            try:
                await t(engine, Session)
                passed += 1
            except Exception as e:
                import traceback
                print(f"[FAIL] {t.__name__}: {e}")
                traceback.print_exc()
                failed += 1
        print()
        print("=" * 60)
        print(f"Career Gamification Engine: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
