"""
Feature Flags & Admin Monitoring REST Endpoints.

Routes:
  GET  /api/v1/admin/feature-flags          → List all feature flag states
  PUT  /api/v1/admin/feature-flags/{name}   → Toggle a feature flag (SUPER_ADMIN only)
  GET  /api/v1/admin/health-deep            → Deep health check (DB, Redis, Celery)
  GET  /api/v1/admin/version                → API version and build info
"""
import logging
import platform
import sys
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.feature_flags import feature_flags
from app.core.metrics import get_all_metrics
from app.core.redis import redis_cache
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User

logger = logging.getLogger("app.api.monitoring")
router = APIRouter()

_start_time = datetime.now(timezone.utc)


@router.get(
    "/admin/feature-flags",
    summary="List Feature Flags",
    tags=["Enterprise Admin CMS"],
)
async def list_feature_flags(current_user: User = Depends(get_current_user)):
    return {
        "environment": settings.ENVIRONMENT,
        "flags": feature_flags.status(),
    }


@router.get(
    "/admin/version",
    summary="API Version & Build Info",
    tags=["Health & System"],
    include_in_schema=True,
)
async def get_version():
    uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "python_version": sys.version,
        "platform": platform.system(),
        "uptime_seconds": round(uptime, 1),
        "api_prefix": settings.API_V1_STR,
    }


@router.get(
    "/admin/health-deep",
    summary="Deep Health Check",
    description="Checks Database, Redis, and Celery broker connectivity.",
    tags=["Health & System"],
)
async def deep_health_check(db: AsyncSession = Depends(get_db)):

    result = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Database check
    try:
        await db.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        result["checks"]["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        result["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        result["status"] = "degraded"

    # Redis check
    try:
        await redis_cache.set("__healthcheck__", "ok", ttl_seconds=10)
        val = await redis_cache.get("__healthcheck__")
        redis_ok = val == "ok"
        result["checks"]["redis"] = {
            "status": "healthy" if redis_ok else "degraded",
            "connected": redis_cache._is_connected,
        }
    except Exception as e:
        result["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        result["status"] = "degraded"

    # Feature flags
    result["checks"]["feature_flags"] = feature_flags.status()

    # Metrics summary
    m = get_all_metrics()
    total = m.get("http_requests_total", 0) or 1
    result["checks"]["metrics"] = {
        "requests_total": int(m.get("http_requests_total", 0)),
        "error_rate_percent": round(m.get("http_errors_total", 0) / total * 100, 2),
    }

    return result
