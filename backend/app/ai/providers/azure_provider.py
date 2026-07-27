"""
Azure OpenAI Provider Stub.
Activate by setting AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL,
AZURE_OPENAI_API_VERSION and LLM_PROVIDER=azure in .env
"""
from typing import AsyncIterator, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Microsoft Azure OpenAI Service provider.
    Install: pip install openai
    """
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self._client = openai.AsyncAzureOpenAI(
                api_key=config.api_key,
                azure_endpoint=config.base_url or "",
                api_version=config.api_version or "2024-02-01",
            )
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    @property
    def provider_name(self) -> str:
        return "azure"

    async def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        azure_msgs = []
        if system_prompt:
            azure_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            azure_msgs.append({"role": m.role, "content": m.content})
        resp = await self._client.chat.completions.create(
            model=self.config.model,          # deployment name on Azure
            messages=azure_msgs,              # type: ignore[arg-type]
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="azure",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        azure_msgs = []
        if system_prompt:
            azure_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            azure_msgs.append({"role": m.role, "content": m.content})
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=azure_msgs,             # type: ignore[arg-type]
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model("gpt-4")
            return len(enc.encode(text))
        except Exception:
            return max(1, len(text) // 4)

    async def is_available(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
