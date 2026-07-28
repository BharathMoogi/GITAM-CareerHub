"""
Sliding Window Rate Limiting Middleware.

Limits requests per-user-IP using an in-memory store
(upgradeable to Redis via RedisCacheManager in production).

Configuration:
  RATE_LIMIT_PER_MINUTE  — Requests allowed per rolling 60-second window.
  RATE_LIMIT_BURST       — Burst allowance on top of per-minute limit.
  FEATURE_RATE_LIMITING  — Feature flag to globally enable/disable.
"""
import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("app.middleware.rate_limit")

# In-memory sliding window store: {client_key: deque of timestamps}
_request_log: Dict[str, Deque[float]] = defaultdict(deque)

# Paths exempt from rate limiting (exact match or prefix match)
EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/api/v1/openapi.json"}
EXEMPT_PREFIXES = ("/landing/", "/uploads/", "/static/")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window rate limiter."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.FEATURE_RATE_LIMITING:
            return await call_next(request)

        path = request.url.path
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Exempt static file prefixes (landing pages, uploads, assets)
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Prefer authenticated user ID if available
        client_key = request.headers.get("X-Real-IP") or request.client.host or "unknown"
        now = time.monotonic()
        window = 60.0
        limit = settings.RATE_LIMIT_PER_MINUTE

        log = _request_log[client_key]

        # Evict old timestamps outside the window
        while log and now - log[0] > window:
            log.popleft()

        if len(log) >= limit:
            logger.warning(f"Rate limit exceeded for client: {client_key}")
            retry_after = int(window - (now - log[0]))
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        log.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(log)))
        return response
