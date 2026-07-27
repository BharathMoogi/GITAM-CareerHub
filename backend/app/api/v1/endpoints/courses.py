from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.course import (
    CourseDetailRead,
    CourseListRead,
    CourseProgressRead,
    SkillDashboardRead,
    UpdateCourseProgressRequest,
)
from app.services.course_service import CourseService

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[List[CourseListRead]],
    summary="List Courses",
    description=(
        "Returns all published courses for the authenticated student's branch, "
        "enriched with lock status and current progress. "
        "Supports optional filters: year, semester, difficulty, and skill name."
    ),
)
async def list_courses(
    year: Optional[int] = Query(None, ge=1, le=4, description="Filter by academic year (1-4)"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester number (1-8)"),
    difficulty: Optional[str] = Query(None, description="BEGINNER, INTERMEDIATE, or ADVANCED"),
    skill: Optional[str] = Query(None, description="Filter by skill name (e.g. Python, STM32)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[CourseListRead]]:
    service = CourseService(db)
    courses = await service.list_courses(
        user_id=current_user.id,
        year=year,
        semester=semester,
        difficulty=difficulty,
        skill_name=skill,
    )
    return APIResponse(
        success=True,
        message=f"{len(courses)} course(s) retrieved successfully",
        data=courses,
    )


@router.get(
    "/{course_id}",
    response_model=APIResponse[CourseDetailRead],
    summary="Get Course Detail",
    description=(
        "Returns full detail for a single course including: "
        "learning objectives, prerequisites, resources, outcomes, skills, and student progress. "
        "Also returns lock status."
    ),
)
async def get_course_detail(
    course_id: str = Path(..., description="Course ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CourseDetailRead]:
    service = CourseService(db)
    course = await service.get_course_detail(user_id=current_user.id, course_id=course_id)
    return APIResponse(
        success=True,
        message="Course retrieved successfully",
        data=course,
    )


@router.patch(
    "/{course_id}/progress",
    response_model=APIResponse[CourseProgressRead],
    summary="Update Course Progress",
    description=(
        "Update the student's progress on a specific course. "
        "Allowed statuses: IN_PROGRESS, COMPLETED. "
        "On COMPLETED:\n"
        "  - StudentCourseProgress is updated.\n"
        "  - StudentSkill scores are automatically calculated.\n"
        "  - Linked RoadmapModule is automatically marked COMPLETED."
    ),
)
async def update_course_progress(
    course_id: str = Path(..., description="Course ID"),
    payload: UpdateCourseProgressRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CourseProgressRead]:
    service = CourseService(db)
    result = await service.update_course_progress(
        user_id=current_user.id,
        course_id=course_id,
        payload=payload,
    )
    return APIResponse(
        success=True,
        message=f"Course progress updated to '{payload.status}' successfully",
        data=result,
    )


@router.get(
    "/skills/my",
    response_model=APIResponse[SkillDashboardRead],
    summary="Get My Skills Dashboard",
    description=(
        "Returns the authenticated student's full skill dashboard: "
        "proficiency scores (0–100), skill categories, source courses, and aggregate stats. "
        "Skills are automatically updated when courses are completed."
    ),
)
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SkillDashboardRead]:
    service = CourseService(db)
    dashboard = await service.get_student_skills(user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Student skills dashboard retrieved successfully",
        data=dashboard,
    )
