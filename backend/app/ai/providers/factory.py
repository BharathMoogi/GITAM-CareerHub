"""
LLM Provider Factory.

Usage:
    config = LLMConfig(provider="mock")
    provider = LLMProviderFactory.create(config)

The factory reads from settings when no explicit config is passed.
To swap providers: change LLM_PROVIDER in .env — zero code changes.
"""
import logging
from typing import Optional
from app.ai.providers.base import BaseLLMProvider, LLMConfig

logger = logging.getLogger("app.ai.providers.factory")

_PROVIDER_REGISTRY: dict = {}


def _register(name: str):
    """Decorator to register a provider class under a string key."""
    def decorator(cls):
        _PROVIDER_REGISTRY[name] = cls
        return cls
    return decorator


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Supported providers (register by key):
      mock    — deterministic mock for testing (no API key needed)
      openai  — OpenAI GPT models
      gemini  — Google Gemini models
      claude  — Anthropic Claude models
      groq    — Groq Cloud (ultra-fast inference)
      azure   — Azure OpenAI Service

    Future:
      ollama  — Local Ollama (self-hosted open-source models)
    """

    @staticmethod
    def create(config: Optional[LLMConfig] = None) -> BaseLLMProvider:
        """
        Instantiate and return the configured provider.

        Args:
            config: LLMConfig with provider name and credentials.
                    If None, reads from application settings.

        Returns:
            A fully initialised BaseLLMProvider instance.

        Raises:
            ValueError if the provider name is not recognised.
        """
        if config is None:
            config = LLMProviderFactory._config_from_settings()

        provider_key = config.provider.lower().strip()
        logger.info(f"Creating LLM provider: {provider_key} / model: {config.model}")

        # Lazy import providers to avoid startup errors when packages not installed
        if provider_key == "mock":
            from app.ai.providers.mock import MockLLMProvider
            return MockLLMProvider(config)

        if provider_key == "openai":
            from app.ai.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)

        if provider_key == "gemini":
            from app.ai.providers.gemini_provider import GeminiProvider
            return GeminiProvider(config)

        if provider_key == "claude":
            from app.ai.providers.claude_provider import ClaudeProvider
            return ClaudeProvider(config)

        if provider_key == "groq":
            from app.ai.providers.groq_provider import GroqProvider
            return GroqProvider(config)

        if provider_key == "azure":
            from app.ai.providers.azure_provider import AzureOpenAIProvider
            return AzureOpenAIProvider(config)

        raise ValueError(
            f"Unknown LLM provider: '{provider_key}'. "
            f"Supported: mock, openai, gemini, claude, groq, azure"
        )

    @staticmethod
    def _config_from_settings() -> LLMConfig:
        """Build LLMConfig from application environment settings."""
        try:
            from app.core.config import settings
            return LLMConfig(
                provider=getattr(settings, "LLM_PROVIDER", "mock"),
                model=getattr(settings, "LLM_MODEL", "mock-v1"),
                api_key=getattr(settings, "LLM_API_KEY", None),
                base_url=getattr(settings, "LLM_BASE_URL", None),
                api_version=getattr(settings, "LLM_API_VERSION", None),
                temperature=float(getattr(settings, "LLM_TEMPERATURE", 0.7)),
                max_tokens=int(getattr(settings, "LLM_MAX_TOKENS", 2048)),
            )
        except Exception:
            # Fallback to mock if settings unavailable
            logger.warning("Could not read LLM settings — falling back to mock provider")
            return LLMConfig(provider="mock", model="mock-v1")

    @staticmethod
    def available_providers() -> list:
        return ["mock", "openai", "gemini", "claude", "groq", "azure"]
