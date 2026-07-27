from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.project import (
    ProjectDetailRead,
    ProjectListRead,
    ProjectProgressRead,
    StudentProjectRead,
    SubmitProjectRequest,
    UpdateProjectProgressRequest,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[List[ProjectListRead]],
    summary="List Projects",
    description=(
        "Returns all published projects for the authenticated student's branch, "
        "enriched with lock status and progress details. "
        "Supports filtering by year, semester, difficulty, technology, skill, and project type."
    ),
)
async def list_projects(
    year: Optional[int] = Query(None, ge=1, le=4, description="Filter by academic year (1-4)"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester number (1-8)"),
    difficulty: Optional[str] = Query(None, description="BEGINNER, INTERMEDIATE, or ADVANCED"),
    technology: Optional[str] = Query(None, description="Filter by technology name (e.g. Python, STM32, SolidWorks)"),
    skill: Optional[str] = Query(None, description="Filter by skill name (e.g. Computer Vision, PCB Design)"),
    project_type: Optional[str] = Query(None, description="MINI, MINOR, MAJOR, or CAPSTONE"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ProjectListRead]]:
    service = ProjectService(db)
    projects = await service.list_projects(
        user_id=current_user.id,
        year=year,
        semester=semester,
        difficulty=difficulty,
        technology=technology,
        skill=skill,
        project_type=project_type,
    )
    return APIResponse(
        success=True,
        message=f"{len(projects)} project(s) retrieved successfully",
        data=projects,
    )


@router.get(
    "/my",
    response_model=APIResponse[List[StudentProjectRead]],
    summary="Get My Projects",
    description="Returns all projects associated with the authenticated student's portfolio and submission status.",
)
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[StudentProjectRead]]:
    service = ProjectService(db)
    my_projects = await service.get_my_projects(user_id=current_user.id)
    return APIResponse(
        success=True,
        message=f"{len(my_projects)} student project(s) retrieved successfully",
        data=my_projects,
    )


@router.get(
    "/{project_id}",
    response_model=APIResponse[ProjectDetailRead],
    summary="Get Project Detail",
    description=(
        "Returns full detail for a single project including: "
        "problem statement, real-world impact, skills, technologies, deliverables, "
        "resources, interview questions, resume points, and submission state."
    ),
)
async def get_project_detail(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectDetailRead]:
    service = ProjectService(db)
    project = await service.get_project_detail(user_id=current_user.id, project_id=project_id)
    return APIResponse(
        success=True,
        message="Project detail retrieved successfully",
        data=project,
    )


@router.patch(
    "/{project_id}/progress",
    response_model=APIResponse[ProjectProgressRead],
    summary="Update Project Progress",
    description="Update progress status (IN_PROGRESS, COMPLETED) for a project.",
)
async def update_project_progress(
    project_id: str = Path(..., description="Project ID"),
    payload: UpdateProjectProgressRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectProgressRead]:
    service = ProjectService(db)
    result = await service.update_project_progress(
        user_id=current_user.id,
        project_id=project_id,
        payload=payload,
    )
    return APIResponse(
        success=True,
        message=f"Project progress updated to '{payload.status}' successfully",
        data=result,
    )


@router.post(
    "/{project_id}/submit",
    response_model=APIResponse[ProjectProgressRead],
    summary="Submit Project",
    description=(
        "Submit a project by attaching GitHub repository, live demo URL, and project report URL. "
        "Automatically updates status, boosts student skill scores, and updates roadmap progress."
    ),
)
async def submit_project(
    project_id: str = Path(..., description="Project ID"),
    payload: SubmitProjectRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectProgressRead]:
    service = ProjectService(db)
    result = await service.submit_project(
        user_id=current_user.id,
        project_id=project_id,
        payload=payload,
    )
    return APIResponse(
        success=True,
        message="Project submitted successfully",
        data=result,
    )
