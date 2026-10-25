from typing import Literal
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    user_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=128)
    endpoint: str = "/chat"

class FeedbackRequest(BaseModel):
    trace_id: str = Field(min_length=1, max_length=64)
    rating: Literal["thumbs_up", "thumbs_down"] | None = None
    correction: str | None = Field(default=None, max_length=5000)

    def model_validate_feedback(self):
        if self.rating is None and not (self.correction and self.correction.strip()):
            raise ValueError("Provide a rating or a non-empty correction")
