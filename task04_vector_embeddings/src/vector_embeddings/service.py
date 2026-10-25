"""Batched embedding service with caching and exponential-backoff retries."""
from __future__ import annotations
import time
from collections.abc import Sequence
from typing import Callable
from .cache import Cache, cache_key, decode_vector, encode_vector, normalize_text
from .providers import EmbeddingProvider

class EmbeddingService:
    def __init__(
        self,
        provider: EmbeddingProvider,
        cache: Cache | None = None,
        batch_size: int = 64,
        max_retries: int = 3,
        base_delay_seconds: float = 0.25,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must not be negative")
        self.provider = provider
        self.cache = cache
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.sleep = sleep

    def _embed_with_retry(self, texts: Sequence[str]) -> list[list[float]]:
        for attempt in range(self.max_retries + 1):
            try:
                vectors = self.provider.embed(texts)
                if len(vectors) != len(texts):
                    raise ValueError("provider returned a different number of vectors than inputs")
                dimensions = {len(v) for v in vectors}
                if len(dimensions) > 1 or any(not v for v in vectors):
                    raise ValueError("provider returned empty or inconsistent vector dimensions")
                return vectors
            except Exception:
            # Retry provider errors and malformed response errors; the last failure propagates.
                if attempt >= self.max_retries:
                    raise
                self.sleep(self.base_delay_seconds * (2 ** attempt))
        raise RuntimeError("unreachable")

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return vectors in input order, using cache hits and bounded provider batches."""
        if not texts:
            return []
        normalized = [normalize_text(text) for text in texts]
        if any(not text for text in normalized):
            raise ValueError("texts must not contain empty strings")
        output: list[list[float] | None] = [None] * len(texts)
        missing_by_key: dict[str, list[int]] = {}
        for i, text in enumerate(normalized):
            key = cache_key(text, self.provider.model_name)
            cached = self.cache.get(key) if self.cache else None
            if cached is not None:
                output[i] = decode_vector(cached)
            else:
                missing_by_key.setdefault(key, []).append(i)

        keys = list(missing_by_key)
        for start in range(0, len(keys), self.batch_size):
            batch_keys = keys[start:start + self.batch_size]
            batch_texts = [normalized[missing_by_key[key][0]] for key in batch_keys]
            vectors = self._embed_with_retry(batch_texts)
            for key, vector in zip(batch_keys, vectors, strict=True):
                for index in missing_by_key[key]:
                    output[index] = [float(value) for value in vector]
                if self.cache:
                    self.cache.set(key, encode_vector([float(value) for value in vector]))
        return [vector for vector in output if vector is not None]
