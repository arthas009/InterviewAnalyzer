from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM.

        Args:
            system_prompt: System message setting the LLM's role.
            user_message: The user's message/question.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens in the response.

        Yields:
            Text chunks as they arrive from the LLM.
        """
        ...

    async def stream_response_with_image(
        self,
        system_prompt: str,
        user_message: str,
        image_base64: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM with an image input.

        Default implementation raises NotImplementedError for non-vision providers.

        Args:
            system_prompt: System message.
            user_message: User's text message.
            image_base64: Base64-encoded JPEG image.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Yields:
            Text chunks.
        """
        raise NotImplementedError(f"{self.provider_name} does not support image input")
        yield  # Make this an async generator

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if the provider is reachable and configured."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider's display name."""
        ...
