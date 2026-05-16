import logging
from typing import Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


def create_provider(
    provider: str,
    openai_api_key: Optional[str] = None,
    openai_model: str = "gpt-4o",
    claude_api_key: Optional[str] = None,
    claude_model: str = "claude-sonnet-4-20250514",
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "llama3",
    gemini_api_key: Optional[str] = None,
    gemini_model: str = "gemini-2.0-flash",
    groq_api_key: Optional[str] = None,
    groq_model: str = "llama-3.3-70b-versatile",
    deepseek_api_key: Optional[str] = None,
    deepseek_model: str = "deepseek-chat",
) -> BaseLLMProvider:
    """Factory function to create the appropriate LLM provider.

    Args:
        provider: One of "openai", "claude", "ollama", "gemini", "groq", "deepseek".
        Other args: Provider-specific configuration.

    Returns:
        Configured LLM provider instance.

    Raises:
        ValueError: If provider is unknown or missing required config.
    """
    if provider == "openai":
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=openai_api_key, model=openai_model)

    elif provider == "claude":
        if not claude_api_key:
            raise ValueError("Claude API key is required")
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(api_key=claude_api_key, model=claude_model)

    elif provider == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(base_url=ollama_base_url, model=ollama_model)

    elif provider == "gemini":
        if not gemini_api_key:
            raise ValueError("Gemini API key is required")
        from .gemini_provider import GeminiProvider
        return GeminiProvider(api_key=gemini_api_key, model=gemini_model)

    elif provider == "groq":
        if not groq_api_key:
            raise ValueError("Groq API key is required")
        from .groq_provider import GroqProvider
        return GroqProvider(api_key=groq_api_key, model=groq_model)

    elif provider == "deepseek":
        if not deepseek_api_key:
            raise ValueError("DeepSeek API key is required")
        from .deepseek_provider import DeepSeekProvider
        return DeepSeekProvider(api_key=deepseek_api_key, model=deepseek_model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Must be 'openai', 'claude', 'ollama', 'gemini', 'groq', or 'deepseek'.")
