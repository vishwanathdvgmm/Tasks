from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    run_id: str
    user_request: str
    plan: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    tool_results: list[str] = Field(default_factory=list)
    draft: str = ""
    review_feedback: list[str] = Field(default_factory=list)
    revision_count: int = 0
    step_count: int = 0
    max_steps: int = 12
    max_revisions: int = 2
    require_approval: bool = False
    approval_id: str | None = None
    approval_decision: Literal["approve", "reject"] | None = None
    status: Literal["running", "paused", "completed", "rejected", "failed"] = "running"
    current_node: str = "planner"
    visited_nodes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    final_output: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
