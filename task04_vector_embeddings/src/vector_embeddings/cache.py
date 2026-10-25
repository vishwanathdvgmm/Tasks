"""Redis cache keyed by normalized text and model identity."""
from __future__ import annotations
import hashlib
import json
import re
from typing import Protocol

def normalize_text(text: str) -> str:
    """Trim and lowercase text; collapse internal whitespace consistently."""
    return re.sub(r"\s+", " ", text.strip().lower())

def cache_key(text: str, model_name: str) -> str:
    """Version/model-scoped SHA-256 key, avoiding collisions across embedding models."""
    normalized = normalize_text(text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    model_digest = hashlib.sha256(model_name.encode("utf-8")).hexdigest()[:12]
    return f"emb:v1:{model_digest}:{digest}"

class Cache(Protocol):
    def get(self, key: str) -> str | bytes | None: ...
    def set(self, key: str, value: str, ex: int | None = None) -> object: ...

class MemoryCache:
    """Small test-friendly cache with Redis-compatible get/set semantics."""
    def __init__(self):
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._data[key] = value
        return True

class RedisCache:
    def __init__(self, url: str = "redis://localhost:6379/0", ttl_seconds: int = 86400 * 30):
        import redis
        self._client = redis.Redis.from_url(url, decode_responses=True)
        self._ttl = ttl_seconds

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> object:
        return self._client.set(key, value, ex=ex or self._ttl)

    def ping(self) -> bool:
        return bool(self._client.ping())

def encode_vector(vector: list[float]) -> str:
    return json.dumps(vector, separators=(",", ":"), allow_nan=False)

def decode_vector(value: str | bytes) -> list[float]:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    decoded = json.loads(value)
    if not isinstance(decoded, list) or not all(isinstance(x, (int, float)) for x in decoded):
        raise ValueError("invalid cached embedding payload")
    return [float(x) for x in decoded]
