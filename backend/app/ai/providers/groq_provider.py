"""
Groq Provider Stub (ultra-fast inference via Groq Cloud).
Activate by setting GROQ_API_KEY and LLM_PROVIDER=groq in .env
"""
from typing import AsyncIterator, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse


class GroqProvider(BaseLLMProvider):
    """
    Groq Cloud provider (llama-3.1-70b-versatile, mixtral-8x7b, etc.).
    Install: pip install groq
    """
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=config.api_key)
        except ImportError:
            raise RuntimeError("groq package not installed. Run: pip install groq")

    @property
    def provider_name(self) -> str:
        return "groq"

    async def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        groq_msgs = []
        if system_prompt:
            groq_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            groq_msgs.append({"role": m.role, "content": m.content})
        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model or "llama-3.1-70b-versatile"),
            messages=groq_msgs,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="groq",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        groq_msgs = []
        if system_prompt:
            groq_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            groq_msgs.append({"role": m.role, "content": m.content})
        stream = await self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model or "llama-3.1-70b-versatile"),
            messages=groq_msgs,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    async def is_available(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
