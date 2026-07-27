from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.schemas.student import (
    BranchRead,
    StudentProfileRead,
    StudentProfileUpdate,
    StudentSocialLinksUpdate,
    TargetRoleRead,
)


class StudentService:
    """
    Business logic layer for Student Profile operations, social links, and master lookup data.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_by_user_id(self, user_id: str) -> Student:
        query = select(Student).where(Student.user_id == user_id)
        result = await self.db.execute(query)
        student = result.scalars().first()
        if not student:
            raise NotFoundException(message=f"Student profile not found for user ID '{user_id}'.")
        return student

    async def get_student_profile(self, user_id: str) -> StudentProfileRead:
        student = await self.get_student_by_user_id(user_id)
        return StudentProfileRead.model_validate(student)

    async def update_student_profile(
        self, user_id: str, data: StudentProfileUpdate
    ) -> StudentProfileRead:
        student = await self.get_student_by_user_id(user_id)

        update_dict = data.model_dump(exclude_unset=True)

        # Validate branch_id if provided
        if "branch_id" in update_dict and update_dict["branch_id"]:
            branch = await self.db.get(Branch, update_dict["branch_id"])
            if not branch:
                raise BadRequestException(message=f"Invalid branch_id '{update_dict['branch_id']}'.")

        # Validate target_role_id if provided
        if "target_role_id" in update_dict and update_dict["target_role_id"]:
            role = await self.db.get(TargetRole, update_dict["target_role_id"])
            if not role:
                raise BadRequestException(message=f"Invalid target_role_id '{update_dict['target_role_id']}'.")

        for key, value in update_dict.items():
            setattr(student, key, value)

        await self.db.commit()
        await self.db.refresh(student)
        return StudentProfileRead.model_validate(student)

    async def update_social_links(
        self, user_id: str, links: StudentSocialLinksUpdate
    ) -> StudentProfileRead:
        student = await self.get_student_by_user_id(user_id)

        links_dict = links.model_dump(exclude_unset=True)
        for key, value in links_dict.items():
            setattr(student, key, value)

        await self.db.commit()
        await self.db.refresh(student)
        return StudentProfileRead.model_validate(student)

    async def update_profile_photo(
        self, user_id: str, photo_path: str
    ) -> StudentProfileRead:
        student = await self.get_student_by_user_id(user_id)
        student.profile_photo = photo_path
        await self.db.commit()
        await self.db.refresh(student)
        return StudentProfileRead.model_validate(student)

    async def list_branches(self) -> List[BranchRead]:
        query = select(Branch).order_by(Branch.name)
        result = await self.db.execute(query)
        branches = result.scalars().all()
        return [BranchRead.model_validate(b) for b in branches]

    async def list_target_roles(self) -> List[TargetRoleRead]:
        query = select(TargetRole).order_by(TargetRole.title)
        result = await self.db.execute(query)
        roles = result.scalars().all()
        return [TargetRoleRead.model_validate(r) for r in roles]
