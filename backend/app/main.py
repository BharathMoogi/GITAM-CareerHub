from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.api.v1.endpoints.refresh import router as refresh_router
from app.core.config import settings
from app.core.exceptions import (
    BaseAppException,
    app_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.metrics import MetricsMiddleware, router as metrics_router
from app.core.redis import redis_cache
from app.database.init_db import init_db
from app.database.session import engine
from app.dependencies.db import get_db
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.schemas.health import HealthResponse
from app.schemas.response import APIResponse
from app.services.health_service import HealthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Production lifespan: setup logging, connect Redis, seed DB, then tear down cleanly.
    """
    setup_logging()
    # Connect to Redis (with fallback to in-memory)
    await redis_cache.connect()
    # Initialize DB & Seed Master Data
    await init_db(engine)
    yield
    # Graceful shutdown
    await engine.dispose()


def create_application() -> FastAPI:
    """
    Production application factory initializing FastAPI with all middlewares,
    routes, security headers, rate limiting, metrics, and exception handlers.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "Production-ready backend API for GITAM CareerHub — "
            "AI-powered career platform featuring Authentication, Student Profiles, "
            "Roadmaps, Learning Engine, Projects, Certifications, Industry Intelligence, "
            "Internship & Placement Engine, AI Mentor, Dashboard Intelligence, "
            "Career Gamification, Resume Intelligence, Notification Engine, "
            "Enterprise Admin CMS, and full DevOps production infrastructure."
        ),
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        contact={
            "name": "GITAM CareerHub Engineering",
            "email": "engineering@gitam.careerhub.edu",
        },
        license_info={"name": "Private — GITAM University"},
    )

    # ── Middleware stack (order matters: outermost wraps all inner layers) ──
    app.add_middleware(SecurityHeadersMiddleware)    # OWASP headers on every response
    app.add_middleware(RateLimitMiddleware)          # Per-IP sliding window rate limiting
    app.add_middleware(MetricsMiddleware)            # Request latency & error tracking
    app.add_middleware(RequestLoggingMiddleware)     # Structured request/response logging
    setup_cors(app)                                 # CORS

    # Static file serving for uploaded profile photos
    os.makedirs(os.path.join("uploads", "profile_photos"), exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # Exception Handlers
    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # ── Routers ──────────────────────────────────────────────────────────────
    # Prometheus metrics endpoint (no auth required)
    app.include_router(metrics_router)

    # Refresh token endpoint
    app.include_router(refresh_router, prefix=settings.API_V1_STR)

    # All versioned API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root Health Check shortcut
    @app.get(
        "/health",
        response_model=APIResponse[HealthResponse],
        tags=["Health & System"],
        summary="Root Health Check",
    )
    async def root_health(db: AsyncSession = Depends(get_db)) -> APIResponse[HealthResponse]:
        health_service = HealthService(db)
        status_data = await health_service.get_health_status()
        return APIResponse(
            success=True,
            message="GITAM CareerHub API is operational",
            data=status_data,
        )

    @app.get("/", tags=["Health & System"], include_in_schema=False)
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "documentation": "/docs",
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False,  # Handled by RequestLoggingMiddleware
    )
