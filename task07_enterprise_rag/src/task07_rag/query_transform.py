from __future__ import annotations
import re

class QueryTransformer:
    """Deterministic mock query expansion and HyDE for no-key local execution."""

    def multi_query(self, question: str) -> list[str]:
        cleaned = question.strip().rstrip("? .")
        candidates = [
            cleaned,
            f"policy and requirements for {cleaned.lower()}",
            f"procedures, eligibility, deadlines, and controls related to {cleaned.lower()}",
        ]
        # Preserve order while removing duplicate variants.
        return list(dict.fromkeys(candidates))[:3]

    def hyde_document(self, question: str) -> str:
        # A real provider would generate a hypothetical answer. This deterministic
        # placeholder intentionally does not assert facts; it supplies query terms.
        terms = re.findall(r"[A-Za-z0-9-]+", question.lower())
        return "Relevant policy or runbook passages about: " + " ".join(terms)
