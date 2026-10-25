from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/vectordb"
    vector_dimensions: int = 1536
    chroma_path: str = "./.chroma"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
