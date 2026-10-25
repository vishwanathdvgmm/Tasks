from typing import Literal
from pydantic import BaseModel, Field, field_validator

MemoryStrategy = Literal["sliding_window", "summary_buffer", "entity"]

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=12000)
    memory_strategy: MemoryStrategy = "sliding_window"

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        import re
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("session_id may contain only letters, digits, underscores, and hyphens")
        return value

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    standalone_query: str
    memory_strategy: MemoryStrategy
    history_tokens: int
    history_messages_used: int

class StoredMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: float
