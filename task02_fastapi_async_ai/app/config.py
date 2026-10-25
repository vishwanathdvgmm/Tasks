from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Async AI Service"
    api_key: str = "dev-secret-key"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    database_url: str = "sqlite+aiosqlite:///./app.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    mock_token_delay_seconds: float = 0.03
    model_name: str = "mock-llm-v1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
