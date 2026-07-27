from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.roadmap import (
    RoadmapModuleRead,
    RoadmapRead,
    StudentProgressRead,
    UpdateModuleProgressRequest,
)
from app.services.roadmap_service import RoadmapService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[List[RoadmapRead]],
    summary="Get Student Roadmaps",
    description=(
        "Returns all active roadmaps for the authenticated student's branch. "
        "Optionally filter by academic year number or semester number. "
        "Future semesters are returned but modules within them will be locked."
    ),
)
async def get_roadmaps(
    year: Optional[int] = Query(None, ge=1, le=4, description="Filter by academic year (1-4)"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester number (1-8)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[RoadmapRead]]:
    service = RoadmapService(db)
    roadmaps = await service.get_roadmaps_for_student(
        user_id=current_user.id, year=year, semester=semester
    )
    return APIResponse(
        success=True,
        message=f"{len(roadmaps)} roadmap(s) retrieved successfully",
        data=roadmaps,
    )


@router.get(
    "/modules",
    response_model=APIResponse[List[RoadmapModuleRead]],
    summary="Get All Roadmap Modules",
    description=(
        "Returns all roadmap modules for the student's branch ordered by display order across semesters. "
        "Each module includes lock status, prerequisites, and student progress state. "
        "Optionally filter to a specific semester."
    ),
)
async def get_modules(
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester number (1-8)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[RoadmapModuleRead]]:
    service = RoadmapService(db)
    modules = await service.get_modules_for_student(
        user_id=current_user.id, semester=semester
    )
    return APIResponse(
        success=True,
        message=f"{len(modules)} module(s) retrieved successfully",
        data=modules,
    )


@router.get(
    "/progress",
    response_model=APIResponse[StudentProgressRead],
    summary="Get Student Roadmap Progress",
    description=(
        "Returns comprehensive progress metrics for the authenticated student including: "
        "overall completion percentage, completed/in-progress/locked/upcoming module lists, "
        "and estimated hours breakdown."
    ),
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentProgressRead]:
    service = RoadmapService(db)
    progress = await service.get_student_progress(user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Student roadmap progress retrieved successfully",
        data=progress,
    )


@router.patch(
    "/progress/{module_id}",
    response_model=APIResponse[RoadmapModuleRead],
    summary="Update Module Progress",
    description=(
        "Update the progress status of a specific roadmap module for the authenticated student. "
        "Allowed statuses: IN_PROGRESS, COMPLETED. "
        "SKIPPED status is restricted to admin/superuser accounts. "
        "Locked modules cannot be updated unless by an admin."
    ),
)
async def update_module_progress(
    module_id: str = Path(..., description="Roadmap Module ID to update progress for"),
    payload: UpdateModuleProgressRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RoadmapModuleRead]:
    service = RoadmapService(db)
    is_admin = current_user.is_superuser or current_user.role == "admin"
    updated = await service.update_module_progress(
        user_id=current_user.id,
        module_id=module_id,
        payload=payload,
        is_admin=is_admin,
    )
    return APIResponse(
        success=True,
        message=f"Module progress updated to '{payload.status}' successfully",
        data=updated,
    )
