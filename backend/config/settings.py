import os
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Literal


def get_data_dir() -> Path:
    """Get the app data directory. Uses --data-dir CLI arg or %APPDATA%/InterviewAnalyzer."""
    import sys
    for i, arg in enumerate(sys.argv):
        if arg == "--data-dir" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return Path(appdata) / "InterviewAnalyzer"


class AudioSettings(BaseModel):
    device_index: Optional[int] = None  # None = default loopback
    sample_rate: int = 16000  # Target sample rate for whisper
    use_microphone: bool = False  # True = use mic instead of system audio


class STTSettings(BaseModel):
    model_size: str = "small"  # tiny, base, small, medium, large-v3
    language: str = "auto"  # Language code or "auto" for auto-detection
    device: str = "auto"  # "auto", "cuda", "cpu"
    compute_type: str = "auto"  # "auto", "float16", "int8", "float32"
    cpu_threads: int = 4  # Max CPU threads for whisper (avoid starving other apps)
    vad_sensitivity: float = 0.4  # Silero VAD threshold (0-1, lower = more sensitive)


class LLMSettings(BaseModel):
    provider: Literal["openai", "claude", "ollama"] = "ollama"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-20250514"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    temperature: float = 0.3
    max_tokens: int = 2048


class AppSettings(BaseModel):
    audio: AudioSettings = Field(default_factory=AudioSettings)
    stt: STTSettings = Field(default_factory=STTSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    language: str = "en"  # UI/interview language

    @classmethod
    def load(cls, data_dir: Optional[Path] = None) -> "AppSettings":
        """Load settings from config.json in data directory."""
        if data_dir is None:
            data_dir = get_data_dir()
        config_path = data_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.model_validate(data)
            except (json.JSONDecodeError, Exception):
                pass
        return cls()

    def save(self, data_dir: Optional[Path] = None) -> None:
        """Save settings to config.json in data directory."""
        if data_dir is None:
            data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        config_path = data_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
