"""
Google Gemini Provider Stub.
Activate by setting GEMINI_API_KEY and LLM_PROVIDER=gemini in .env
"""
from typing import AsyncIterator, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider (gemini-1.5-pro, gemini-1.5-flash, etc.).
    Install: pip install google-generativeai
    """
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(config.model or "gemini-1.5-flash")
        except ImportError:
            raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _to_gemini_history(self, messages: List[ChatMessage]):
        history = []
        for m in messages[:-1]:  # All but the last (which is the current turn)
            history.append({
                "role": "user" if m.role == "user" else "model",
                "parts": [m.content],
            })
        return history

    async def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        user_msg = messages[-1].content if messages else ""
        history = self._to_gemini_history(messages)
        chat = self._model.start_chat(history=history)
        response = await chat.send_message_async(user_msg)
        content = response.text
        total_tokens = len(content.split()) * 2
        return LLMResponse(
            content=content,
            model=self.config.model,
            provider="gemini",
            total_tokens=total_tokens,
        )

    async def stream(self, messages: List[ChatMessage], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        user_msg = messages[-1].content if messages else ""
        history = self._to_gemini_history(messages)
        chat = self._model.start_chat(history=history)
        async for chunk in await chat.send_message_async(user_msg, stream=True):
            yield chunk.text

    async def count_tokens(self, text: str) -> int:
        result = self._model.count_tokens(text)
        return result.total_tokens

    async def is_available(self) -> bool:
        try:
            self._genai.list_models()
            return True
        except Exception:
            return False
