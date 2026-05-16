import logging
from typing import AsyncGenerator

from google import genai
from google.genai import types

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider with streaming support."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            if response.text:
                yield response.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def check_connection(self) -> bool:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents="Hi",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini connection check failed: {e}")
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
            import base64
            image_bytes = base64.b64decode(image_base64)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=[user_message, image_part],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            if response.text:
                yield response.text

        except Exception as e:
            logger.error(f"Gemini vision streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self._model})"
