from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class AnswerEnvelope(StrictModel):
    answer: str = Field(min_length=1, max_length=4000)
    confidence: Literal["low", "medium", "high"]
    sources: list[str] = Field(max_length=10)

class ToolArguments(StrictModel):
    """Base class for strict tool argument schemas."""

class CalculatorArgs(ToolArguments):
    expression: str = Field(min_length=1, max_length=120, description="Arithmetic expression")

class WeatherArgs(ToolArguments):
    city: str = Field(min_length=1, max_length=80)

class SearchArgs(ToolArguments):
    query: str = Field(min_length=2, max_length=200)

class SqlArgs(ToolArguments):
    query_name: Literal["demo_users"] = Field(
        description="Only the predefined demo_users read-only query is supported"
    )

class ToolResult(StrictModel):
    ok: bool
    result: object | None = None
    error: str | None = None
