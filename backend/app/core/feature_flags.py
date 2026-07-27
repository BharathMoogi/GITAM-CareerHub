"""
Feature Flag System — Runtime On/Off toggles for GITAM CareerHub.

Flags are driven by Settings (config.py) and can be toggled at runtime
via environment variables without a code deploy.

Usage:
    from app.core.feature_flags import feature_flags, require_feature

    @require_feature("ai_mentor")
    async def my_endpoint(...):
        ...
"""
import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger("app.core.feature_flags")


class FeatureFlags:
    """Central feature flag registry backed by environment configuration."""

    @property
    def ai_mentor(self) -> bool:
        return settings.FEATURE_AI_MENTOR

    @property
    def gamification(self) -> bool:
        return settings.FEATURE_GAMIFICATION

    @property
    def resume_ai(self) -> bool:
        return settings.FEATURE_RESUME_AI

    @property
    def notifications(self) -> bool:
        return settings.FEATURE_NOTIFICATIONS

    @property
    def analytics(self) -> bool:
        return settings.FEATURE_ANALYTICS

    @property
    def rate_limiting(self) -> bool:
        return settings.FEATURE_RATE_LIMITING

    def is_enabled(self, flag_name: str) -> bool:
        return getattr(self, flag_name, False)

    def status(self) -> dict:
        return {
            "ai_mentor": self.ai_mentor,
            "gamification": self.gamification,
            "resume_ai": self.resume_ai,
            "notifications": self.notifications,
            "analytics": self.analytics,
            "rate_limiting": self.rate_limiting,
        }


feature_flags = FeatureFlags()


def require_feature(flag_name: str):
    """Decorator that gates an endpoint behind a feature flag."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not feature_flags.is_enabled(flag_name):
                raise HTTPException(status_code=503, detail=f"Feature '{flag_name}' is currently disabled.")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
