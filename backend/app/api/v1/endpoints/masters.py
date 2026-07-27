from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.schemas.response import APIResponse
from app.schemas.student import BranchRead, TargetRoleRead
from app.services.student_service import StudentService

router = APIRouter()


@router.get(
    "/branches",
    response_model=APIResponse[List[BranchRead]],
    summary="List Engineering Branches",
    description="Retrieve all engineering branch options (AIML, ECE, EEE, Mechanical).",
)
async def get_branches(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[BranchRead]]:
    service = StudentService(db)
    branches = await service.list_branches()
    return APIResponse(
        success=True,
        message="Branches retrieved successfully",
        data=branches,
    )


@router.get(
    "/target-roles",
    response_model=APIResponse[List[TargetRoleRead]],
    summary="List Target Engineering Roles",
    description="Retrieve all target role options (Embedded Engineer, VLSI Engineer, AI Engineer, Data Scientist, etc.).",
)
async def get_target_roles(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[TargetRoleRead]]:
    service = StudentService(db)
    roles = await service.list_target_roles()
    return APIResponse(
        success=True,
        message="Target roles retrieved successfully",
        data=roles,
    )
