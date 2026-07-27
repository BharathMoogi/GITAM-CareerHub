"""
LLM Provider Abstraction Layer — Base Interface.

All LLM provider implementations must inherit from BaseLLMProvider.
Business logic (tools, services) only depends on this interface,
so any provider can be swapped without changing application code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any


@dataclass
class ChatMessage:
    """A single message in a conversation history."""
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMResponse:
    """Structured response from any LLM provider."""
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    raw: Optional[Dict[str, Any]] = None

    @property
    def token_usage(self) -> int:
        return self.total_tokens


@dataclass
class LLMConfig:
    """
    Provider-agnostic configuration.
    Each provider picks the fields it needs.
    """
    provider: str                          # openai | gemini | claude | groq | azure | mock
    model: str = "gpt-4o-mini"            # default model name
    api_key: Optional[str] = None
    base_url: Optional[str] = None        # for Azure / Ollama
    api_version: Optional[str] = None     # for Azure
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Implement this to add a new provider — no other code changes needed.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. 'openai', 'gemini')."""

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send a conversation to the LLM and return a complete response.

        Args:
            messages: Conversation history (user + assistant turns).
            system_prompt: Optional override for the system message.
            **kwargs: Provider-specific overrides (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with content, token usage, and metadata.
        """

    @abstractmethod
    async def stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a response token-by-token.
        Each yielded value is a string fragment of the assistant reply.
        """

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a given text string.
        Used for context window management.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Health check — returns True if the provider is reachable.
        Called during startup and health checks.
        """

    def build_messages(
        self,
        history: List[ChatMessage],
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> List[ChatMessage]:
        """
        Utility: Prepend system prompt and append the latest user message
        to the conversation history.
        """
        msgs: List[ChatMessage] = []
        if system_prompt:
            msgs.append(ChatMessage(role="system", content=system_prompt))
        msgs.extend(history)
        msgs.append(ChatMessage(role="user", content=user_message))
        return msgs
