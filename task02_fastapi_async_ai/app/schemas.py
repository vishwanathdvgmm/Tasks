from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=8000)
    max_tokens: int = Field(default=128, ge=1, le=1024)
    temperature: float = Field(default=0.7, ge=0, le=2)
    stream: bool = True
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,64}$")

    @field_validator("prompt")
    @classmethod
    def prompt_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must contain non-whitespace characters")
        return value.strip()

class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input: str | list[str] = Field(min_length=1)

    @field_validator("input")
    @classmethod
    def validate_input(cls, value):
        items = [value] if isinstance(value, str) else value
        if not items or any(not isinstance(x, str) or not x.strip() for x in items):
            raise ValueError("each input text must contain non-whitespace characters")
        if any(len(x) > 8000 for x in items):
            raise ValueError("each input text must be at most 8000 characters")
        return value

class EmbeddingItem(BaseModel):
    object: Literal["embedding"] = "embedding"
    index: int
    embedding: list[float]

class EmbeddingResponse(BaseModel):
    object: Literal["list"] = "list"
    model: str = "mock-embedding-v1"
    data: list[EmbeddingItem]

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
