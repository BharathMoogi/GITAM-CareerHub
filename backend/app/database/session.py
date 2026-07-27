"""
Production Database Session with Connection Pooling.

Uses SQLAlchemy async engine with:
  - AsyncAdaptedQueuePool for PostgreSQL (configurable pool_size, max_overflow)
  - StaticPool for SQLite in testing
  - Connection health check (pool_pre_ping=True)
"""
import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, StaticPool

from app.core.config import settings

logger = logging.getLogger("app.database.session")

# Determine if we're in test mode
IS_TESTING = os.getenv("TESTING", "false").lower() == "true"

if IS_TESTING or "sqlite" in (settings.DATABASE_URL or ""):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
        poolclass=StaticPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {"application_name": "gitam-careerhub-api"},
            "command_timeout": 30,
        } if "asyncpg" in settings.DATABASE_URL else {},
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

logger.info(
    f"Database engine initialized: pool_size={settings.DB_POOL_SIZE}, "
    f"max_overflow={settings.DB_MAX_OVERFLOW}, pool_pre_ping=True"
)
