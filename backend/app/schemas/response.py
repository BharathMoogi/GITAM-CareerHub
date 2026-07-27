from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


def get_current_utc_timestamp() -> str:
    """Return ISO formatted UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API Response Envelope for all endpoints.
    Always includes success status, message, data payload, and UTC timestamp.
    """
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    timestamp: str = Field(default_factory=get_current_utc_timestamp)


class ErrorDetail(BaseModel):
    message: str
    code: str
    details: Optional[dict] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    timestamp: str = Field(default_factory=get_current_utc_timestamp)
