from dataclasses import dataclass
from .config import INPUT_USD_PER_MILLION, OUTPUT_USD_PER_MILLION

@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

def estimate_tokens(text: str) -> int:
    # Lightweight demo approximation. Replace with provider-reported token counts in production.
    return max(1, (len(text) + 3) // 4) if text else 0

def calculate_usage(prompt_tokens: int, completion_tokens: int) -> Usage:
    cost = (
        prompt_tokens * INPUT_USD_PER_MILLION
        + completion_tokens * OUTPUT_USD_PER_MILLION
    ) / 1_000_000
    return Usage(prompt_tokens, completion_tokens, round(cost, 10))
