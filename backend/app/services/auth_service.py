from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.exceptions import UnauthorizedException, BadRequestException
from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.schemas.auth import LoginRequest, RegisterRequest, Token, UserRead


class AuthService:
    """
    Business logic layer for Authentication, Student Registration, & Token issuance.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = (
            select(User)
            .options(
                joinedload(User.student_profile).joinedload(Student.branch),
                joinedload(User.student_profile).joinedload(Student.target_role),
            )
            .where(User.email == email.lower().strip())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_student_by_roll_number(self, roll_number: str) -> Optional[Student]:
        query = select(Student).where(Student.roll_number == roll_number.upper().strip())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def register_student(self, data: RegisterRequest) -> UserRead:
        email_clean = data.email.lower().strip()
        roll_number_clean = data.roll_number.upper().strip()

        # Validate duplicate email
        existing_user = await self.get_user_by_email(email_clean)
        if existing_user:
            raise BadRequestException(message=f"Account with email '{email_clean}' already exists.")

        # Validate duplicate roll number
        existing_student = await self.get_student_by_roll_number(roll_number_clean)
        if existing_student:
            raise BadRequestException(message=f"Student with roll number '{roll_number_clean}' already exists.")

        # Validate branch_id exists
        branch = await self.db.get(Branch, data.branch_id)
        if not branch:
            raise BadRequestException(message=f"Invalid branch_id '{data.branch_id}'. Branch not found.")

        # Validate target_role_id exists
        target_role = await self.db.get(TargetRole, data.target_role_id)
        if not target_role:
            raise BadRequestException(message=f"Invalid target_role_id '{data.target_role_id}'. Target role not found.")

        # Create User record
        user = User(
            email=email_clean,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name.strip(),
            role="student",
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()

        # Create linked Student Profile record
        student = Student(
            user_id=user.id,
            full_name=data.full_name.strip(),
            email=email_clean,
            roll_number=roll_number_clean,
            phone_number=data.phone_number.strip() if data.phone_number else None,
            branch_id=data.branch_id,
            target_role_id=data.target_role_id,
            current_year=data.current_year,
            semester=data.semester,
            github_url=data.github_url,
            linkedin_url=data.linkedin_url,
            leetcode_url=data.leetcode_url,
            hackerrank_url=data.hackerrank_url,
            is_active=True,
        )
        self.db.add(student)
        await self.db.commit()

        # Re-fetch user with full eager loading for UserRead schema validation
        user_loaded = await self.get_user_by_email(email_clean)
        return UserRead.model_validate(user_loaded)

    async def authenticate_user(self, login_data: LoginRequest) -> Token:
        user = await self.get_user_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException(message="Invalid email or password credentials.")
        
        if not user.is_active:
            raise UnauthorizedException(message="User account is inactive.")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.role},
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,
        )
