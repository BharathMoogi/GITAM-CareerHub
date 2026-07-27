from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token, UserRead
from app.schemas.response import APIResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register New Student",
    description="Register a new student account with email, roll number, academic details, and password. Validates duplicate email and roll number.",
)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserRead]:
    auth_service = AuthService(db)
    user_data = await auth_service.register_student(register_data)
    return APIResponse(
        success=True,
        message="Student registered successfully",
        data=user_data,
    )


@router.post(
    "/login",
    response_model=APIResponse[Token],
    summary="User Login & JWT Token Generation",
    description="Authenticate student user with email and password credentials to obtain a Bearer JWT access token.",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Token]:
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(login_data)
    return APIResponse(
        success=True,
        message="Authentication successful",
        data=token,
    )


@router.get(
    "/me",
    response_model=APIResponse[UserRead],
    summary="Get Current Authenticated User Profile",
    description="Retrieve account & student profile details of the currently authenticated user based on Bearer token.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserRead]:
    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=UserRead.model_validate(current_user),
    )


@router.post(
    "/logout",
    response_model=APIResponse[dict],
    summary="User Logout",
    description="Logout the currently authenticated user (client should discard the JWT Bearer token).",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:
    return APIResponse(
        success=True,
        message="Logged out successfully",
        data={"user_id": current_user.id},
    )
