from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key: str = os.getenv("LLM_API_KEY", "ollama")
    model: str = os.getenv("LLM_MODEL", "qwen2.5:3b")
    timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

settings = Settings()
