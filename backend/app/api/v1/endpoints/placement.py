"""
Internship & Placement Engine — REST Endpoints.

Routes:
  GET  /internships                  → List all active internships (with eligibility flags)
  GET  /internships/{id}             → Internship detail
  GET  /placements                   → List all active placement jobs
  GET  /placements/{id}              → Placement job detail
  GET  /applications                 → My applications (with filters)
  POST /applications/apply           → Submit application (eligibility enforced)
  PATCH /applications/{id}/status    → Update application stage
  GET  /applications/history         → Full application history
  GET  /applications/dashboard       → Summary stats + active listings
  GET  /applications/offers          → My offer letters
  PATCH /applications/offers/{id}/accept → Accept / decline an offer
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.placement import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusUpdate,
    InternshipDetailRead,
    InternshipListRead,
    OfferLetterRead,
    PlacementDashboard,
    PlacementJobDetailRead,
    PlacementJobListRead,
)
from app.services.placement_service import PlacementService

router = APIRouter()


# ─── Internships ──────────────────────────────────────────────────────────────

@router.get(
    "/internships",
    response_model=APIResponse[List[InternshipListRead]],
    summary="List Internships",
    description=(
        "Returns all active internship postings with eligibility flags for the authenticated student. "
        "Eligible internships appear first. Filterable by mode (REMOTE/HYBRID/ONSITE) and type."
    ),
)
async def list_internships(
    status: str = Query("ACTIVE", description="ACTIVE / CLOSED / UPCOMING"),
    mode: Optional[str] = Query(None, description="REMOTE / HYBRID / ONSITE"),
    internship_type: Optional[str] = Query(None, description="TECHNICAL / RESEARCH / MANAGEMENT / DESIGN / DATA"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[InternshipListRead]]:
    service = PlacementService(db)
    internships = await service.list_internships(
        user_id=current_user.id,
        status=status, mode=mode,
        internship_type=internship_type, company_id=company_id,
    )
    return APIResponse(
        success=True,
        message=f"{len(internships)} internship(s) retrieved",
        data=internships,
    )


@router.get(
    "/internships/{id}",
    response_model=APIResponse[InternshipDetailRead],
    summary="Get Internship Detail",
    description="Full internship detail including eligibility breakdown and student readiness score.",
)
async def get_internship_detail(
    id: str = Path(..., description="Internship ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InternshipDetailRead]:
    service = PlacementService(db)
    detail = await service.get_internship_detail(user_id=current_user.id, internship_id=id)
    return APIResponse(success=True, message="Internship detail retrieved", data=detail)


# ─── Placements ───────────────────────────────────────────────────────────────

@router.get(
    "/placements",
    response_model=APIResponse[List[PlacementJobListRead]],
    summary="List Placement Jobs",
    description=(
        "Returns all active placement job postings with eligibility flags for the authenticated student. "
        "Higher package jobs appear first among eligible ones."
    ),
)
async def list_placements(
    status: str = Query("ACTIVE", description="ACTIVE / CLOSED"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[PlacementJobListRead]]:
    service = PlacementService(db)
    jobs = await service.list_placements(user_id=current_user.id, status=status, company_id=company_id)
    return APIResponse(
        success=True,
        message=f"{len(jobs)} placement job(s) retrieved",
        data=jobs,
    )


@router.get(
    "/placements/{id}",
    response_model=APIResponse[PlacementJobDetailRead],
    summary="Get Placement Job Detail",
    description="Full placement job detail including eligibility and student readiness score.",
)
async def get_placement_detail(
    id: str = Path(..., description="Placement Job ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlacementJobDetailRead]:
    service = PlacementService(db)
    detail = await service.get_placement_detail(user_id=current_user.id, placement_id=id)
    return APIResponse(success=True, message="Placement job detail retrieved", data=detail)


# ─── Applications ─────────────────────────────────────────────────────────────

@router.get(
    "/applications",
    response_model=APIResponse[List[ApplicationRead]],
    summary="My Applications",
    description=(
        "Returns the authenticated student's applications. "
        "Optionally filter by status (APPLIED/SHORTLISTED/...) or type (INTERNSHIP/PLACEMENT)."
    ),
)
async def get_my_applications(
    status: Optional[str] = Query(None, description="Filter by application status"),
    application_type: Optional[str] = Query(None, description="INTERNSHIP or PLACEMENT"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ApplicationRead]]:
    service = PlacementService(db)
    apps = await service.get_my_applications(
        user_id=current_user.id, status=status, application_type=application_type
    )
    return APIResponse(success=True, message=f"{len(apps)} application(s) found", data=apps)


@router.post(
    "/applications/apply",
    response_model=APIResponse[ApplicationRead],
    summary="Apply for Internship / Placement",
    description=(
        "Submit an application for an internship or placement job. "
        "Eligibility is validated before applying: "
        "readiness score, branch, CGPA. "
        "Duplicate applications are rejected."
    ),
    status_code=201,
)
async def apply(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ApplicationRead]:
    service = PlacementService(db)
    app = await service.apply(user_id=current_user.id, payload=payload)
    return APIResponse(success=True, message="Application submitted successfully", data=app)


@router.patch(
    "/applications/{id}/status",
    response_model=APIResponse[ApplicationRead],
    summary="Update Application Status",
    description=(
        "Advance or reject an application stage. "
        "Valid transitions: APPLIED→SHORTLISTED→ONLINE_TEST→TECHNICAL→HR→SELECTED/REJECTED. "
        "Automatically generates an offer letter when status is SELECTED."
    ),
)
async def update_application_status(
    id: str = Path(..., description="Application ID"),
    payload: ApplicationStatusUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ApplicationRead]:
    service = PlacementService(db)
    app = await service.update_status(application_id=id, payload=payload)
    return APIResponse(success=True, message=f"Application status updated to {payload.status}", data=app)


@router.get(
    "/applications/history",
    response_model=APIResponse[List[ApplicationRead]],
    summary="Application History",
    description="Full application history for the authenticated student, ordered by most recent update.",
)
async def get_application_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ApplicationRead]]:
    service = PlacementService(db)
    apps = await service.get_my_applications(user_id=current_user.id)
    return APIResponse(success=True, message=f"{len(apps)} application(s) in history", data=apps)


@router.get(
    "/applications/dashboard",
    response_model=APIResponse[PlacementDashboard],
    summary="Placement Dashboard",
    description=(
        "Returns a complete placement dashboard: "
        "application summary stats, recent applications, "
        "top active internships and placement jobs with eligibility context."
    ),
)
async def get_placement_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlacementDashboard]:
    service = PlacementService(db)
    dashboard = await service.get_dashboard(user_id=current_user.id)
    return APIResponse(success=True, message="Placement dashboard retrieved", data=dashboard)


@router.get(
    "/applications/offers",
    response_model=APIResponse[List[OfferLetterRead]],
    summary="My Offer Letters",
    description="Returns all offer letters issued to the authenticated student.",
)
async def get_offer_letters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[OfferLetterRead]]:
    service = PlacementService(db)
    offers = await service.get_offer_letters(user_id=current_user.id)
    return APIResponse(success=True, message=f"{len(offers)} offer(s) found", data=offers)


@router.patch(
    "/applications/offers/{id}/accept",
    response_model=APIResponse[OfferLetterRead],
    summary="Accept / Decline Offer Letter",
    description="Accept (true) or decline (false) a specific offer letter.",
)
async def accept_offer(
    id: str = Path(..., description="Offer Letter ID"),
    accept: bool = Query(..., description="true to accept, false to decline"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[OfferLetterRead]:
    service = PlacementService(db)
    offer = await service.accept_offer(user_id=current_user.id, offer_id=id, accept=accept)
    action = "accepted" if accept else "declined"
    return APIResponse(success=True, message=f"Offer letter {action}", data=offer)
