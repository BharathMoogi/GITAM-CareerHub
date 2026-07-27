import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.student import (
    StudentProfileRead,
    StudentProfileUpdate,
    StudentSocialLinksUpdate,
)
from app.services.student_service import StudentService

router = APIRouter()

UPLOAD_DIR = os.path.join("uploads", "profile_photos")


@router.get(
    "/me",
    response_model=APIResponse[StudentProfileRead],
    summary="View Student Profile",
    description="Retrieve the complete academic and professional profile of the authenticated student.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentProfileRead]:
    service = StudentService(db)
    profile = await service.get_student_profile(current_user.id)
    return APIResponse(
        success=True,
        message="Student profile retrieved successfully",
        data=profile,
    )


@router.put(
    "/me",
    response_model=APIResponse[StudentProfileRead],
    summary="Update Student Profile",
    description="Update academic and personal details (full_name, phone_number, branch_id, target_role_id, current_year, semester).",
)
async def update_my_profile(
    update_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentProfileRead]:
    service = StudentService(db)
    updated_profile = await service.update_student_profile(current_user.id, update_data)
    return APIResponse(
        success=True,
        message="Student profile updated successfully",
        data=updated_profile,
    )


@router.patch(
    "/me/social-links",
    response_model=APIResponse[StudentProfileRead],
    summary="Update Student Social Links",
    description="Update GitHub, LinkedIn, LeetCode, and HackerRank profile URLs. Validates GitHub and LinkedIn format.",
)
async def update_my_social_links(
    links_data: StudentSocialLinksUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentProfileRead]:
    service = StudentService(db)
    updated_profile = await service.update_social_links(current_user.id, links_data)
    return APIResponse(
        success=True,
        message="Social links updated successfully",
        data=updated_profile,
    )


@router.post(
    "/me/photo",
    response_model=APIResponse[StudentProfileRead],
    summary="Upload Profile Photo",
    description="Upload profile photo image file and update the student profile with the stored file path.",
)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StudentProfileRead]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
        
    relative_path = f"/uploads/profile_photos/{unique_filename}"

    service = StudentService(db)
    updated_profile = await service.update_profile_photo(current_user.id, relative_path)
    return APIResponse(
        success=True,
        message="Profile photo uploaded successfully",
        data=updated_profile,
    )
