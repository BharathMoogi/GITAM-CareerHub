from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check detailed response.
    """
    status: str = Field(..., example="healthy")
    environment: str = Field(..., example="development")
    version: str = Field(..., example="0.1.0")
    database: Dict[str, str] = Field(
        ...,
        example={"status": "connected", "latency_ms": "1.23"},
    )
