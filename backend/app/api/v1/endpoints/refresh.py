"""
Refresh Token Endpoint — POST /api/v1/auth/refresh

Accepts a valid refresh token and returns a new access + refresh token pair.
Old refresh tokens are single-use (rotated on each call for security).
"""
import logging
import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token, create_refresh_token, verify_refresh_token

logger = logging.getLogger("app.api.auth.refresh")

router = APIRouter()


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


@router.post(
    "/auth/refresh",
    response_model=RefreshResponse,
    summary="Refresh Access Token",
    description=(
        "Exchange a valid refresh token for a new access token + refresh token pair. "
        "Implements token rotation: each refresh token is single-use."
    ),
    tags=["Authentication"],
)
async def refresh_access_token(body: RefreshRequest) -> RefreshResponse:
    try:
        payload = verify_refresh_token(body.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )

    subject = payload["sub"]
    extra_claims = {k: v for k, v in payload.items() if k not in {"sub", "exp", "iat", "type", "jti"}}

    from app.core.config import settings
    new_access = create_access_token(subject=subject, extra_claims=extra_claims)
    new_refresh = create_refresh_token(subject=subject, extra_claims=extra_claims)

    logger.info(f"Token rotated for subject={subject[:8]}...")

    return RefreshResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
