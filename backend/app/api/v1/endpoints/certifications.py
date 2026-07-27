from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.certification import (
    CertificationDetailRead,
    CertificationListRead,
    CertificationProgressRead,
    StudentCertificationRead,
    SubmitCertificationRequest,
    UpdateCertificationProgressRequest,
)
from app.services.certification_service import CertificationService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[List[CertificationListRead]],
    summary="List Certifications",
    description=(
        "Returns all published certifications for the authenticated student's branch, "
        "enriched with 5-way lock status and user completion state. "
        "Supports filtering by semester, difficulty, provider, and skill."
    ),
)
async def list_certifications(
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester number (1-8)"),
    difficulty: Optional[str] = Query(None, description="BEGINNER, INTERMEDIATE, or ADVANCED"),
    provider: Optional[str] = Query(None, description="Filter by provider (e.g. NPTEL, AWS, Cisco, Microsoft, Google, Texas Instruments, NVIDIA)"),
    skill: Optional[str] = Query(None, description="Filter by skill name (e.g. TensorFlow, C Programming, SolidWorks)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[CertificationListRead]]:
    service = CertificationService(db)
    certs = await service.list_certifications(
        user_id=current_user.id,
        semester=semester,
        difficulty=difficulty,
        provider=provider,
        skill=skill,
    )
    return APIResponse(
        success=True,
        message=f"{len(certs)} certification(s) retrieved successfully",
        data=certs,
    )


@router.get(
    "/my",
    response_model=APIResponse[List[StudentCertificationRead]],
    summary="Get My Certifications",
    description="Returns all certifications associated with the authenticated student's portfolio and verification status.",
)
async def get_my_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[StudentCertificationRead]]:
    service = CertificationService(db)
    my_certs = await service.get_my_certifications(user_id=current_user.id)
    return APIResponse(
        success=True,
        message=f"{len(my_certs)} student certification(s) retrieved successfully",
        data=my_certs,
    )


@router.get(
    "/{id}",
    response_model=APIResponse[CertificationDetailRead],
    summary="Get Certification Detail",
    description=(
        "Returns full detail for a single certification including: "
        "prerequisites, benefits, exam pattern, official links, skills, lock status, and student progress."
    ),
)
async def get_certification_detail(
    id: str = Path(..., description="Certification ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CertificationDetailRead]:
    service = CertificationService(db)
    cert = await service.get_certification_detail(user_id=current_user.id, certification_id=id)
    return APIResponse(
        success=True,
        message="Certification detail retrieved successfully",
        data=cert,
    )


@router.patch(
    "/{id}/progress",
    response_model=APIResponse[CertificationProgressRead],
    summary="Update Certification Progress",
    description="Update progress status (IN_PROGRESS, COMPLETED) for a certification.",
)
async def update_certification_progress(
    id: str = Path(..., description="Certification ID"),
    payload: UpdateCertificationProgressRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CertificationProgressRead]:
    service = CertificationService(db)
    result = await service.update_certification_progress(
        user_id=current_user.id,
        certification_id=id,
        payload=payload,
    )
    return APIResponse(
        success=True,
        message=f"Certification progress updated to '{payload.status}' successfully",
        data=result,
    )


@router.post(
    "/{id}/submit",
    response_model=APIResponse[CertificationProgressRead],
    summary="Submit Certification",
    description=(
        "Submit a earned certification by uploading Certificate URL, Verification ID, exam score, and issue date. "
        "Automatically updates status to COMPLETED, verifies certificate, boosts student skills, updates roadmap progress, "
        "calculates placement readiness score, and unlocks internship eligibility."
    ),
)
async def submit_certification(
    id: str = Path(..., description="Certification ID"),
    payload: SubmitCertificationRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CertificationProgressRead]:
    service = CertificationService(db)
    result = await service.submit_certification(
        user_id=current_user.id,
        certification_id=id,
        payload=payload,
    )
    return APIResponse(
        success=True,
        message="Certification submitted and verified successfully",
        data=result,
    )
