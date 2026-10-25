from __future__ import annotations
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    source_filename: str
    page_number: int = Field(ge=1)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)

class RetrievedChunk(DocumentChunk):
    score: float
    retrieval_method: str = "hybrid"

class Citation(BaseModel):
    chunk_id: str
    source_filename: str
    page_number: int
    quote: str

class AnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    multi_query: bool = True
    hyde: bool = True

class AnswerResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    confidence: str
    fallback_used: bool = False
    query_variations: list[str] = Field(default_factory=list)
    pipeline: list[str] = Field(default_factory=list)
