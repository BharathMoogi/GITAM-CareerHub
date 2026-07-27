"""
RBAC Middleware — Role-Based Access Control enforcement.

Validates JWT access tokens on every protected request and enforces
role-level permission guards. Integrates with the FastAPI dependency system.

RBAC Hierarchy:
  SUPER_ADMIN > COLLEGE_ADMIN > DEPARTMENT_ADMIN > PLACEMENT_OFFICER > FACULTY > MODERATOR > STUDENT
"""
import logging
from typing import List, Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_token

logger = logging.getLogger("app.middleware.rbac")

# Role hierarchy for permission escalation checks
ROLE_HIERARCHY = {
    "SUPER_ADMIN": 100,
    "COLLEGE_ADMIN": 80,
    "DEPARTMENT_ADMIN": 60,
    "PLACEMENT_OFFICER": 50,
    "FACULTY": 40,
    "MODERATOR": 30,
    "STUDENT": 10,
}

_bearer = HTTPBearer(auto_error=False)


def get_role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role.upper(), 0)


def has_minimum_role(user_role: str, minimum_role: str) -> bool:
    """Returns True if user_role is equal or higher in hierarchy than minimum_role."""
    return get_role_level(user_role) >= get_role_level(minimum_role)


async def extract_token_payload(request: Request) -> Optional[dict]:
    """Extract and decode JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split("Bearer ")[-1].strip()
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory that enforces role-based access.

    Usage:
        @router.get("/admin/...", dependencies=[Depends(require_role("SUPER_ADMIN", "COLLEGE_ADMIN"))])
        async def admin_endpoint(...):
            ...
    """
    async def dependency(request: Request):
        payload = await extract_token_payload(request)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

        user_role = payload.get("role", "STUDENT")
        if user_role not in [r.upper() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return payload

    return dependency


def require_minimum_role(minimum_role: str):
    """
    FastAPI dependency factory that enforces hierarchical role access.
    Any role >= minimum_role in hierarchy is allowed.
    """
    async def dependency(request: Request):
        payload = await extract_token_payload(request)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

        user_role = payload.get("role", "STUDENT")
        if not has_minimum_role(user_role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Minimum required role: {minimum_role}",
            )
        return payload

    return dependency
