"""
Career Gamification Engine — Database Models.

Tables:
  Achievement      : Master achievements list
  Badge            : Master badge definitions
  StudentBadge     : Awarded badges mapping
  StudentXP        : XP tracking, current level, streak, and level title
  Level            : Level thresholds (Level 1-6)
  DailyChallenge   : Daily active challenges
  WeeklyChallenge  : Weekly active challenges
  MonthlyChallenge : Monthly active challenges
  Reward           : Unlockable rewards
  CareerMilestone  : Milestones earned along the journey
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Level(Base):
    """Level definitions mapping XP thresholds to Level Titles."""
    __tablename__ = "gamification_levels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    level_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    min_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Achievement(Base):
    """Master achievement definitions."""
    __tablename__ = "gamification_achievements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERAL")
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Badge(Base):
    """Master badge definitions."""
    __tablename__ = "gamification_badges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False, default="BRONZE", comment="BRONZE / SILVER / GOLD / PLATINUM / DIAMOND")
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="ACADEMIC")
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class StudentBadge(Base):
    """Badges awarded to students."""
    __tablename__ = "gamification_student_badges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id: Mapped[str] = mapped_column(String(36), ForeignKey("gamification_badges.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    badge: Mapped["Badge"] = relationship("Badge", lazy="select")


class StudentXP(Base):
    """Student XP summary, current level, and streak tracking."""
    __tablename__ = "gamification_student_xp"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    level_title: Mapped[str] = mapped_column(String(100), nullable=False, default="Explorer")
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())


class DailyChallenge(Base):
    """Daily challenge tasks for XP rewards."""
    __tablename__ = "gamification_daily_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="DAILY")
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)


class WeeklyChallenge(Base):
    """Weekly challenge tasks for XP rewards."""
    __tablename__ = "gamification_weekly_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=150)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="WEEKLY")
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)


class MonthlyChallenge(Base):
    """Monthly challenge tasks for XP rewards."""
    __tablename__ = "gamification_monthly_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=400)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="MONTHLY")
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)


class Reward(Base):
    """Unlockable rewards achievable using level/XP or milestone triggers."""
    __tablename__ = "gamification_rewards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    min_level_required: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False, default="VOUCHER", comment="VOUCHER / BADGE_FRAME / REFERRAL / PROFILE_HIGHLIGHT")
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class CareerMilestone(Base):
    """Career milestone timeline records for students."""
    __tablename__ = "gamification_milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERAL")
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
