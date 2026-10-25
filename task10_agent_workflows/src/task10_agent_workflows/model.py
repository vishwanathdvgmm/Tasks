from __future__ import annotations

import re

class MockModel:
    """Deterministic mock model; swap this adapter for a real LLM if desired."""

    def plan(self, request: str) -> list[str]:
        plan = ["Retrieve relevant workflow information", "Execute any requested calculation or safe tool", "Review output against the request"]
        if re.search(r"delete|transfer|send|destructive|commit", request, re.I):
            plan.insert(2, "Request human approval before any high-impact action")
        return plan

    def draft(self, request: str, evidence: list[str], results: list[str], feedback: list[str]) -> str:
        parts = [f"Request: {request}"]
        if evidence:
            parts.append("Evidence:\n- " + "\n- ".join(evidence))
        if results:
            parts.append("Tool results:\n- " + "\n- ".join(results))
        if feedback:
            parts.append("Applied reviewer feedback:\n- " + "\n- ".join(feedback))
        parts.append("Conclusion: the workflow gathered evidence, ran only allow-listed tools, and produced a reviewable result.")
        return "\n\n".join(parts)

    def review(self, draft: str, request: str, revision_count: int) -> tuple[bool, str]:
        if not draft.strip():
            return False, "Draft is empty; produce a non-empty answer."
        if "Request:" not in draft or "Conclusion:" not in draft:
            return False, "Draft is missing required request or conclusion sections."
        # Deliberately inject one review failure for requests containing this marker
        # so the reflection loop can be demonstrated deterministically.
        if "[force-review-retry]" in request and revision_count == 0:
            return False, "Demonstration retry: add the reviewer feedback to the final draft."
        return True, "Required sections and non-empty output verified."
