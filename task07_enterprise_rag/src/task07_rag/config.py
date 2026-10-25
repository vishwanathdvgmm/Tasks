from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    backend: str = os.getenv("RAG_BACKEND", "memory")
    score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.18"))
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    database_url: str = os.getenv("DATABASE_URL", "")

settings = Settings()
