"""
Anthropic Claude Provider Stub.
Activate by setting ANTHROPIC_API_KEY and LLM_PROVIDER=claude in .env
"""
from typing import AsyncIterator, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude provider (claude-3-5-sonnet, claude-3-haiku, etc.).
    Install: pip install anthropic
    """
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=config.api_key)
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    @property
    def provider_name(self) -> str:
        return "claude"

    async def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        import anthropic
        anthropic_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        resp = await self._client.messages.create(
            model=kwargs.get("model", self.config.model or "claude-3-5-sonnet-20241022"),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system_prompt or "",
            messages=anthropic_msgs,
        )
        content = resp.content[0].text if resp.content else ""
        return LLMResponse(
            content=content,
            model=resp.model,
            provider="claude",
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
            total_tokens=resp.usage.input_tokens + resp.usage.output_tokens,
            finish_reason=resp.stop_reason or "stop",
        )

    async def stream(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        anthropic_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        async with self._client.messages.stream(
            model=kwargs.get("model", self.config.model or "claude-3-5-sonnet-20241022"),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system_prompt or "",
            messages=anthropic_msgs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    async def is_available(self) -> bool:
        try:
            await self._client.messages.create(
                model=self.config.model or "claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
