from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.dependencies.db import get_db
from app.models.user import User
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts, decodes, and verifies the JWT token from the Authorization header.
    Returns the authenticated User model.
    """
    if not token:
        raise UnauthorizedException(message="Not authenticated. Missing Authorization header.")

    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException(message="Invalid token or token has expired.")

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(message="Token payload is missing subject.")

    auth_service = AuthService(db)
    user = await db.get(User, user_id)
    
    if not user:
        raise UnauthorizedException(message="User associated with token no longer exists.")
    
    if not user.is_active:
        raise UnauthorizedException(message="User account is deactivated.")

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency ensuring the current authenticated user has administrative privileges.
    """
    if not current_user.is_superuser:
        raise ForbiddenException(message="Superuser privileges required for this action.")
    return current_user
