import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("app.middleware.request_logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that measures request process time and logs execution duration.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time = time.perf_counter() - start_time
        process_time_ms = round(process_time * 1000, 2)
        
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {process_time_ms}ms"
        )
        
        return response
