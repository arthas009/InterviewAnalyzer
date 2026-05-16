import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq provider with streaming support. Uses OpenAI-compatible API."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self._model = model

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def check_connection(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Groq connection check failed: {e}")
            return False

    @property
    def provider_name(self) -> str:
        return f"Groq ({self._model})"
