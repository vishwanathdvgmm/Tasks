from collections import Counter
import re
from app.token_budget import TokenBudget

class MemoryManager:
    def __init__(self, token_budget: TokenBudget):
        self.budget = token_budget

    def sliding_window(self, messages: list[dict], max_turns: int = 6) -> list[dict]:
        # A turn is one user message and its following assistant response.
        recent = messages[-max_turns * 2:]
        return self.budget.trim(recent)

    def summary_buffer(self, messages: list[dict], summary: str = "", max_recent_messages: int = 6) -> tuple[str, list[dict]]:
        recent = messages[-max_recent_messages:]
        older = messages[:-max_recent_messages] if len(messages) > max_recent_messages else []
        if older:
            # Deterministic fallback summary; an LLM provider can improve it in production.
            snippets = [f"{m['role']}: {m['content'][:180]}" for m in older[-8:]]
            summary = (summary + "\n" + "\n".join(snippets)).strip()
            summary = summary[-3000:]
        return summary, self.budget.trim(recent)

    def entity_memory(self, messages: list[dict], entities: dict[str, str] | None = None) -> tuple[dict[str, str], list[dict]]:
        entities = dict(entities or {})
        # Lightweight demo extraction for named entities and simple product-like names.
        patterns = [
            r"\b(?:I am comparing|we use|I use|about)\s+([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2})",
            r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2})\s+(?:plan|subscription|product|service)\b",
        ]
        for msg in messages[-12:]:
            if msg.get("role") != "user":
                continue
            for pattern in patterns:
                for match in re.findall(pattern, msg.get("content", "")):
                    entities[match.strip()] = msg["content"][:240]
        return entities, self.budget.trim(messages[-6:])

    def build_context(self, strategy: str, messages: list[dict], summary: str = "", entities: dict | None = None):
        if strategy == "summary_buffer":
            new_summary, recent = self.summary_buffer(messages, summary)
            return {"summary": new_summary, "entities": entities or {}, "messages": recent}
        if strategy == "entity":
            new_entities, recent = self.entity_memory(messages, entities)
            return {"summary": summary, "entities": new_entities, "messages": recent}
        return {"summary": summary, "entities": entities or {}, "messages": self.sliding_window(messages)}
