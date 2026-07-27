"""
Dashboard Intelligence Engine — REST API Endpoints.

Routes:
  GET /dashboard/student         → Comprehensive Student Command Center Dashboard
  GET /dashboard/faculty         → Faculty Department Analytics & Student Progress
  GET /dashboard/placement       → Placement Officer Funnels & Company Eligibility
  GET /dashboard/admin           → Superadmin Platform Stats, DAU/MAU & System Health
  GET /dashboard/leaderboard     → Student Performance Rankings
  GET /dashboard/recent-activity → Real-time Activity Feed
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    StudentDashboardResponse,
    FacultyDashboardResponse,
    PlacementDashboardResponse,
    AdminDashboardResponse,
    LeaderboardResponse,
    RecentActivityItem,
)
from app.core.exceptions import ForbiddenException

logger = logging.getLogger("app.api.dashboard")
router = APIRouter()


# ── 1. Student Dashboard ──────────────────────────────────────────────────────

@router.get(
    "/dashboard/student",
    response_model=StudentDashboardResponse,
    summary="Student Command Center Dashboard",
    description="Returns full student command center metrics calculated live from all 8 engines.",
)
async def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_student_dashboard(user_id=current_user.id)
    return StudentDashboardResponse(**result)


# ── 2. Faculty Dashboard ──────────────────────────────────────────────────────

@router.get(
    "/dashboard/faculty",
    response_model=FacultyDashboardResponse,
    summary="Faculty Department Analytics",
    description="Returns department-wide student progress, skill heatmaps, risk alerts, and leaderboards.",
)
async def get_faculty_dashboard(
    branch_code: Optional[str] = Query(None, description="Branch code filter (e.g. AIML, ECE)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("FACULTY", "ADMIN"):
        raise ForbiddenException("Faculty or Admin access required for faculty dashboard")

    service = DashboardService(db)
    result = await service.get_faculty_dashboard(user_id=current_user.id, branch_code=branch_code or "AIML")
    return FacultyDashboardResponse(**result)


# ── 3. Placement Officer Dashboard ────────────────────────────────────────────

@router.get(
    "/dashboard/placement",
    response_model=PlacementDashboardResponse,
    summary="Placement Officer Command Center",
    description="Returns hiring funnels, company eligibility, placement rates, and upcoming drive schedules.",
)
async def get_placement_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("PLACEMENT_OFFICER", "ADMIN"):
        raise ForbiddenException("Placement Officer or Admin access required")

    service = DashboardService(db)
    result = await service.get_placement_dashboard()
    return PlacementDashboardResponse(**result)


# ── 4. Admin Dashboard ────────────────────────────────────────────────────────

@router.get(
    "/dashboard/admin",
    response_model=AdminDashboardResponse,
    summary="Superadmin System & Platform Stats",
    description="Returns DAU/WAU/MAU, API throughput, system health, and database metrics.",
)
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("Superadmin access required")

    service = DashboardService(db)
    result = await service.get_admin_dashboard()
    return AdminDashboardResponse(**result)


# ── 5. Leaderboard ────────────────────────────────────────────────────────────

@router.get(
    "/dashboard/leaderboard",
    response_model=LeaderboardResponse,
    summary="Student Performance Leaderboard",
    description="Returns top student rankings calculated from career readiness and skill scores.",
)
async def get_leaderboard(
    branch_code: Optional[str] = Query(None, description="Optional branch filter (e.g. AIML)"),
    limit: int = Query(20, ge=1, le=100, description="Max leaderboard rows"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_leaderboard(branch_code=branch_code, limit=limit)
    return LeaderboardResponse(**result)


# ── 6. Recent Activity Feed ───────────────────────────────────────────────────

@router.get(
    "/dashboard/recent-activity",
    response_model=List[RecentActivityItem],
    summary="Real-time Student Activity Feed",
    description="Returns real-time feed of courses completed, applications submitted, and AI sessions.",
)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    results = await service.get_recent_activity(user_id=current_user.id, limit=limit)
    return [RecentActivityItem(**item) for item in results]
