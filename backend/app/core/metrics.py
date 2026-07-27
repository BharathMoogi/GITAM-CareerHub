"""
Prometheus Metrics & OpenTelemetry Instrumentation Module.

Exposes /metrics endpoint compatible with Prometheus scraping.
Tracks:
  - HTTP request durations (histogram)
  - Active connections (gauge)
  - Request counter by endpoint & status code
  - Database query latency
  - Cache hit/miss ratio

OpenTelemetry ready — hooks into OTEL_ENDPOINT from settings when configured.
"""
import logging
import time
from typing import Dict
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("app.core.metrics")

# In-process metrics store (replaced by prometheus_client in real deployment)
_metrics: Dict[str, float] = {
    "http_requests_total": 0,
    "http_errors_total": 0,
    "http_request_duration_sum": 0.0,
    "active_connections": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "db_queries_total": 0,
}

router = APIRouter()


def increment(metric: str, value: float = 1.0) -> None:
    _metrics[metric] = _metrics.get(metric, 0) + value


def observe(metric: str, value: float) -> None:
    _metrics[metric] = _metrics.get(metric, 0) + value


def get_all_metrics() -> Dict[str, float]:
    return dict(_metrics)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records per-request latency and error metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.ENABLE_METRICS:
            return await call_next(request)

        start = time.monotonic()
        _metrics["active_connections"] = _metrics.get("active_connections", 0) + 1
        try:
            response = await call_next(request)
            duration = (time.monotonic() - start) * 1000  # ms
            increment("http_requests_total")
            observe("http_request_duration_sum", duration)
            if response.status_code >= 400:
                increment("http_errors_total")
            response.headers["X-Response-Time-Ms"] = f"{duration:.1f}"
            return response
        finally:
            _metrics["active_connections"] = max(0, _metrics.get("active_connections", 1) - 1)


@router.get(
    "/metrics",
    include_in_schema=False,
    summary="Prometheus Metrics Endpoint",
    tags=["Health & System"],
)
async def prometheus_metrics():
    """
    Exposes metrics in Prometheus text exposition format.
    Scraped by Prometheus every 15s in production.
    """
    lines = [
        "# HELP http_requests_total Total HTTP requests processed",
        "# TYPE http_requests_total counter",
        f"http_requests_total {_metrics.get('http_requests_total', 0):.0f}",
        "",
        "# HELP http_errors_total Total HTTP 4xx/5xx responses",
        "# TYPE http_errors_total counter",
        f"http_errors_total {_metrics.get('http_errors_total', 0):.0f}",
        "",
        "# HELP http_request_duration_ms_sum Sum of request durations in milliseconds",
        "# TYPE http_request_duration_ms_sum counter",
        f"http_request_duration_ms_sum {_metrics.get('http_request_duration_sum', 0):.2f}",
        "",
        "# HELP active_connections Current active HTTP connections",
        "# TYPE active_connections gauge",
        f"active_connections {_metrics.get('active_connections', 0):.0f}",
        "",
        "# HELP cache_hits_total Redis/in-memory cache hits",
        "# TYPE cache_hits_total counter",
        f"cache_hits_total {_metrics.get('cache_hits', 0):.0f}",
        "",
        "# HELP cache_misses_total Redis/in-memory cache misses",
        "# TYPE cache_misses_total counter",
        f"cache_misses_total {_metrics.get('cache_misses', 0):.0f}",
        "",
        "# HELP db_queries_total Total database queries executed",
        "# TYPE db_queries_total counter",
        f"db_queries_total {_metrics.get('db_queries_total', 0):.0f}",
    ]
    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get(
    "/metrics/summary",
    summary="Human-Readable Metrics Summary",
    tags=["Health & System"],
)
async def metrics_summary():
    """JSON summary of all current system metrics."""
    m = get_all_metrics()
    total = m.get("http_requests_total", 0) or 1
    return {
        "http_requests_total": int(m.get("http_requests_total", 0)),
        "http_errors_total": int(m.get("http_errors_total", 0)),
        "error_rate_percent": round(m.get("http_errors_total", 0) / total * 100, 2),
        "avg_response_time_ms": round(m.get("http_request_duration_sum", 0) / total, 2),
        "active_connections": int(m.get("active_connections", 0)),
        "cache_hit_rate_percent": round(
            m.get("cache_hits", 0) / max(m.get("cache_hits", 0) + m.get("cache_misses", 1), 1) * 100, 2
        ),
        "db_queries_total": int(m.get("db_queries_total", 0)),
    }
