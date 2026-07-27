"""
Career Gamification Engine — REST API Endpoints.

Routes:
  GET  /gamification/xp                       → Student XP breakdown, current level, and streak
  GET  /gamification/badges                   → Student's earned & available badges
  GET  /gamification/leaderboard              → Filterable leaderboards (college, department, branch, semester)
  GET  /gamification/challenges               → Active daily, weekly, and monthly challenges
  POST /gamification/challenges/{id}/claim    → Claim challenge XP reward
  GET  /gamification/milestones               → Career milestone timeline
  GET  /gamification/rewards                  → Unlockable rewards & redemption status
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.gamification_service import GamificationService
from app.schemas.gamification import (
    StudentXPResponse, BadgesResponse, ChallengesResponse, ClaimChallengeResponse,
    MilestoneItem, RewardItem, GamificationLeaderboardResponse
)

logger = logging.getLogger("app.api.gamification")
router = APIRouter()


@router.get(
    "/gamification/xp",
    response_model=StudentXPResponse,
    summary="Get My XP & Level Status",
    description="Returns total XP, current level, level title (Explorer to Industry Ready), streak days, and XP to next level.",
)
async def get_xp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    result = await service.get_student_xp(user_id=current_user.id)
    return StudentXPResponse(**result)


@router.get(
    "/gamification/badges",
    response_model=BadgesResponse,
    summary="Get My Badges",
    description="Returns earned badges and available unlockable badges across Bronze, Silver, Gold, Platinum, Diamond tiers.",
)
async def get_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    result = await service.get_badges(user_id=current_user.id)
    return BadgesResponse(**result)


@router.get(
    "/gamification/leaderboard",
    response_model=GamificationLeaderboardResponse,
    summary="Gamification Leaderboard Rankings",
    description="Returns top student rankings filterable by scope (college, department, branch, semester).",
)
async def get_leaderboard(
    scope: str = Query("college", description="Scope: college / department / branch / semester"),
    branch_code: Optional[str] = Query(None, description="Optional branch code (e.g. AIML)"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Optional semester filter"),
    limit: int = Query(20, ge=1, le=100, description="Max entries to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    result = await service.get_leaderboard(scope=scope, branch_code=branch_code, semester=semester, limit=limit)
    return GamificationLeaderboardResponse(**result)


@router.get(
    "/gamification/challenges",
    response_model=ChallengesResponse,
    summary="Active Gamification Challenges",
    description="Returns active Daily, Weekly, and Monthly challenges with XP rewards.",
)
async def get_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    result = await service.get_challenges()
    return ChallengesResponse(**result)


@router.post(
    "/gamification/challenges/{challenge_id}/claim",
    response_model=ClaimChallengeResponse,
    summary="Claim Challenge XP Reward",
    description="Claims XP for a completed daily/weekly/monthly challenge.",
)
async def claim_challenge(
    challenge_id: str = Path(..., description="Challenge ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    result = await service.claim_challenge(user_id=current_user.id, challenge_id=challenge_id)
    return ClaimChallengeResponse(**result)


@router.get(
    "/gamification/milestones",
    response_model=List[MilestoneItem],
    summary="Career Milestone Timeline",
    description="Returns student's career milestone timeline.",
)
async def get_milestones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    results = await service.get_milestones(user_id=current_user.id)
    return [MilestoneItem(**item) for item in results]


@router.get(
    "/gamification/rewards",
    response_model=List[RewardItem],
    summary="Unlockable Rewards Store",
    description="Returns unlockable rewards (resume review vouchers, mock interview passes, referral priority, badge frames).",
)
async def get_rewards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    results = await service.get_rewards(user_id=current_user.id)
    return [RewardItem(**item) for item in results]
