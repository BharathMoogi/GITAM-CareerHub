import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.schemas.health import HealthResponse


class HealthService:
    """
    Service responsible for system health checks and database readiness verification.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_health_status(self) -> HealthResponse:
        db_status = "disconnected"
        latency_str = "0"
        
        try:
            start_time = time.perf_counter()
            await self.db.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start_time) * 1000
            db_status = "connected"
            latency_str = f"{latency_ms:.2f}ms"
        except Exception as err:
            db_status = f"unhealthy: {str(err)}"

        return HealthResponse(
            status="healthy" if db_status == "connected" else "degraded",
            environment=settings.ENVIRONMENT,
            version="0.1.0",
            database={
                "status": db_status,
                "latency": latency_str,
            },
        )
