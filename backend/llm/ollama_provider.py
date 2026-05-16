import logging
from typing import AsyncGenerator

import httpx

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider with streaming support."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                        "stream": True,
                    },
                ) as response:
                    if response.status_code != 200:
                        yield f"\n[Error: Ollama returned status {response.status_code}]"
                        return

                    import json
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                if content:
                                    yield content
                            if data.get("done", False):
                                break
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama. Is it running?")
            yield "\n[Error: Cannot connect to Ollama. Make sure it's running on " + self._base_url + "]"
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False

    @property
    def provider_name(self) -> str:
        return f"Ollama ({self._model})"
