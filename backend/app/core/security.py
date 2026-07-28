"""
JWT Security — Access Token + Refresh Token implementation.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger("app.core.security")

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: Any, extra_claims: Optional[Dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any, extra_claims: Optional[Dict] = None) -> str:
    """Long-lived refresh token for silent re-authentication."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# Backward-compatible alias used by app.dependencies.auth
def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode an access token; returns None on any error (safe fallback for auth dependency)."""
    try:
        payload = decode_token(token)
        if payload.get("type") not in ("access", None):
            return None
        return payload
    except Exception:
        return None


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Decode and validate that a token is a refresh token."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token is not a refresh token")
    return payload

