from pydantic import BaseModel, ConfigDict, Field


class GoldenExample(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1)
    ground_truth: str = Field(min_length=1)
    contexts: list[str] = Field(default_factory=list)
    source_id: str = "demo"

class EvalScores(BaseModel):
    faithfulness: float = Field(ge=0, le=1)
    answer_relevance: float = Field(ge=0, le=1)
    context_precision: float = Field(ge=0, le=1)
    context_recall: float = Field(ge=0, le=1)
