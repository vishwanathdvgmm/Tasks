from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 86400
    max_history_tokens: int = 1000
    max_completion_tokens: int = 500
    token_encoding: str = "cl100k_base"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
