import tiktoken

class TokenCounter:
    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except ValueError as exc:
            raise ValueError(f"Unknown tiktoken encoding: {encoding_name}") from exc
        self.encoding_name = encoding_name

    def count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def split_to_budget(self, text: str, max_tokens: int) -> list[str]:
        """Hard-cap fallback: split by token IDs, preserving exact tokenizer boundaries."""
        if max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        ids = self.encoding.encode(text)
        return [
            self.encoding.decode(ids[i:i + max_tokens])
            for i in range(0, len(ids), max_tokens)
        ] if ids else []
