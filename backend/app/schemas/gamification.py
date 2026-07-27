"""
Pydantic schemas for Career Gamification Engine API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StudentXPResponse(BaseModel):
    student_id: str
    total_xp: int
    current_level: int
    level_title: str
    min_xp_for_current_level: int
    next_level_min_xp: int
    progress_percentage: float
    streak_days: int
    last_activity_date: Optional[str] = None


class BadgeItem(BaseModel):
    badge_id: str
    code: str
    name: str
    description: str
    tier: str
    category: str
    icon_url: Optional[str] = None
    awarded_at: Optional[str] = None
    is_unlocked: Optional[bool] = None


class BadgesResponse(BaseModel):
    total_earned: int
    earned_badges: List[BadgeItem]
    all_badges: List[BadgeItem]


class ChallengeItem(BaseModel):
    id: str
    title: str
    description: str
    xp_reward: int
    expires_at: str


class ChallengesResponse(BaseModel):
    daily_challenges: List[ChallengeItem]
    weekly_challenges: List[ChallengeItem]
    monthly_challenges: List[ChallengeItem]


class ClaimChallengeResponse(BaseModel):
    challenge_id: str
    title: str
    xp_awarded: int
    new_total_xp: int
    current_level: int
    message: str


class MilestoneItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    achieved_at: str


class RewardItem(BaseModel):
    reward_id: str
    title: str
    description: str
    min_level_required: int
    xp_cost: int
    reward_type: str
    is_unlocked: bool
    can_afford: bool


class LeaderboardEntry(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    branch_code: str
    avatar_url: Optional[str] = None
    total_xp: int
    current_level: int
    level_title: str
    rank: int


class GamificationLeaderboardResponse(BaseModel):
    scope: str
    branch_code: Optional[str] = None
    semester: Optional[int] = None
    total_entries: int
    leaderboard: List[LeaderboardEntry]
