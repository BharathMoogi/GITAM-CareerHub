from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.schemas.health import HealthResponse
from app.schemas.response import APIResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=APIResponse[HealthResponse],
    summary="API & Database Health Check",
    description="Check operational status and connectivity of the API application and PostgreSQL database.",
)
async def check_health(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HealthResponse]:
    health_service = HealthService(db)
    status_data = await health_service.get_health_status()
    return APIResponse(
        success=True,
        message="Health status retrieved successfully",
        data=status_data,
    )
