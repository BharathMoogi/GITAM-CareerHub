"""
OpenAI Provider Stub.
Activate by setting OPENAI_API_KEY and LLM_PROVIDER=openai in .env
"""
from typing import AsyncIterator, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider (GPT-3.5-turbo, GPT-4, GPT-4o, etc.).
    Install: pip install openai
    """
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self._client = openai.AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        from openai.types.chat import ChatCompletionMessageParam
        oai_msgs: List[ChatCompletionMessageParam] = []
        if system_prompt:
            oai_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            oai_msgs.append({"role": m.role, "content": m.content})  # type: ignore[arg-type]

        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=oai_msgs,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="openai",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        oai_msgs = []
        if system_prompt:
            oai_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            oai_msgs.append({"role": m.role, "content": m.content})

        stream = await self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=oai_msgs,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.config.model)
            return len(enc.encode(text))
        except Exception:
            return len(text) // 4

    async def is_available(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
