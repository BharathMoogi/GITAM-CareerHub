from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.company import (
    CompanyDetailRead,
    CompanyListRead,
    StudentReadinessSummaryRead,
)
from app.services.industry_service import IndustryService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[List[CompanyListRead]],
    summary="List Companies",
    description=(
        "Returns all companies with student readiness context. "
        "Each company card shows: readiness score (0-100), readiness label "
        "(WEAK / MODERATE / STRONG / READY), skill match count, job roles, and top required skills. "
        "Supports filtering by industry, hiring status, and skill name."
    ),
)
async def list_companies(
    industry: Optional[str] = Query(None, description="Filter by industry (e.g. Semiconductors, Automotive, IT)"),
    is_hiring: Optional[bool] = Query(None, description="Filter to only actively hiring companies"),
    skill: Optional[str] = Query(None, description="Filter companies that require a specific skill (e.g. Python, STM32)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[CompanyListRead]]:
    service = IndustryService(db)
    companies = await service.list_companies(
        user_id=current_user.id,
        industry=industry,
        is_hiring=is_hiring,
        skill=skill,
    )
    return APIResponse(
        success=True,
        message=f"{len(companies)} company/companies retrieved successfully",
        data=companies,
    )


@router.get(
    "/my-readiness",
    response_model=APIResponse[StudentReadinessSummaryRead],
    summary="My Industry Readiness Dashboard",
    description=(
        "Returns the authenticated student's readiness dashboard across all companies. "
        "Includes: average readiness score, top company match, and per-company "
        "breakdown with gap analysis (skills to acquire)."
    ),
)
async def get_my_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentReadinessSummaryRead]:
    service = IndustryService(db)
    summary = await service.get_my_readiness(user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Industry readiness dashboard retrieved successfully",
        data=summary,
    )


@router.get(
    "/{id}",
    response_model=APIResponse[CompanyDetailRead],
    summary="Get Company Intelligence Detail",
    description=(
        "Returns full company intelligence: "
        "job roles, required skills with gap analysis, "
        "recommended courses / projects / certifications, "
        "interview rounds and question bank, "
        "5-axis readiness breakdown (course, project, skill, certification scores). "
        "Also persists the readiness score to the student profile."
    ),
)
async def get_company_detail(
    id: str = Path(..., description="Company ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CompanyDetailRead]:
    service = IndustryService(db)
    detail = await service.get_company_detail(user_id=current_user.id, company_id=id)
    return APIResponse(
        success=True,
        message="Company intelligence retrieved successfully",
        data=detail,
    )
