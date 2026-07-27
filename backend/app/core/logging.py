"""
Structured JSON Logging Setup — Production ready.
Supports local pretty-print in DEBUG mode and JSON-structured output in production.
Readable by Fluentd, Loki, Datadog, and CloudWatch log parsers.
"""
import sys
import json
import logging
import traceback
from datetime import datetime, timezone
from app.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """JSON structured formatter for production log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.ENVIRONMENT,
            "service": "gitam-careerhub-api",
            "version": settings.VERSION,
        }
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        return json.dumps(log_obj)


class PrettyConsoleFormatter(logging.Formatter):
    """Human-readable formatter for local development."""
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        return f"{color}[{ts}] {record.levelname:<8} {record.name}: {record.getMessage()}{self.RESET}"


def setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(PrettyConsoleFormatter())

    root_logger.addHandler(handler)

    # Suppress noisy libraries
    for lib in ["uvicorn.access", "sqlalchemy.engine", "httpcore", "httpx"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    logging.getLogger("app").setLevel(level)
