import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider with streaming support."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._client = AsyncOpenAI(api_key=api_key)
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
            logger.error(f"OpenAI streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def check_connection(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI connection check failed: {e}")
            return False

    async def stream_response_with_image(
        self,
        system_prompt: str,
        user_message: str,
        image_base64: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI vision streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self._model})"
