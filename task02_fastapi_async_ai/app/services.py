import asyncio
import hashlib
import math
from collections.abc import AsyncIterator
from app.config import settings

async def mock_token_stream(prompt: str, max_tokens: int) -> AsyncIterator[str]:
    for token in f"Mock response: {prompt}".split()[:max_tokens]:
        await asyncio.sleep(settings.mock_token_delay_seconds)
        yield token + " "

def mock_embedding(text: str, dimensions: int = 16) -> list[float]:
    raw = hashlib.sha256(text.encode()).digest()
    values = [(raw[i] / 255 * 2) - 1 for i in range(dimensions)]
    norm = math.sqrt(sum(v * v for v in values)) or 1
    return [round(v / norm, 6) for v in values]
