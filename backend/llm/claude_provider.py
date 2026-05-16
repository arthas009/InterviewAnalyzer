import logging
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider with streaming support."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        try:
            async with self._client.messages.stream(
                model=self._model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def check_connection(self) -> bool:
        try:
            # Simple test message to verify API key
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception as e:
            logger.warning(f"Claude connection check failed: {e}")
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
            async with self._client.messages.stream(
                model=self._model,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": user_message},
                        ],
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude vision streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    @property
    def provider_name(self) -> str:
        return f"Claude ({self._model})"
