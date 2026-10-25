import tiktoken
from app.config import settings

class TokenBudget:
    """Counts approximate chat tokens and trims oldest complete messages first."""
    def __init__(self, max_tokens: int | None = None, encoding_name: str | None = None):
        self.max_tokens = max_tokens or settings.max_history_tokens
        try:
            self.encoding = tiktoken.get_encoding(encoding_name or settings.token_encoding)
        except (ValueError, KeyError):
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_text(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        # Conservative approximation; actual chat serialization varies by model.
        return sum(4 + self.count_text(str(m.get("role", ""))) + self.count_text(str(m.get("content", ""))) for m in messages)

    def trim(self, messages: list[dict]) -> list[dict]:
        kept = list(messages)
        while kept and self.count_messages(kept) > self.max_tokens:
            kept.pop(0)
        return kept
