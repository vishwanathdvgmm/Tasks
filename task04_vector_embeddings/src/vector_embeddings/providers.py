"""Embedding provider implementations.

The mock provider is deterministic and offline, but its vectors are for engineering
tests only: they are not semantically meaningful embeddings.
"""
from __future__ import annotations
import hashlib
import os
from typing import Protocol, Sequence
import numpy as np

class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

class MockEmbeddingProvider:
    """Create deterministic, fixed-dimensional pseudo-embeddings without network calls."""
    def __init__(self, dimensions: int = 32):
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions
        self.calls = 0

    @property
    def model_name(self) -> str:
        return f"mock-hash-{self.dimensions}d-v1"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        vectors = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(self.dimensions)
            vec /= np.linalg.norm(vec)
            vectors.append(vec.astype(float).tolist())
        return vectors

class OpenAIEmbeddingProvider:
    """Adapter for OpenAI's embeddings endpoint."""
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import OpenAI
        self._model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("Set OPENAI_API_KEY before using the OpenAI provider")
        self._client = OpenAI(api_key=key)

    @property
    def model_name(self) -> str:
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=list(texts))
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

class SentenceTransformersProvider:
    """Adapter for a local Hugging Face Sentence-Transformers model."""
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Install local-model dependencies with: uv sync --extra local"
            ) from exc
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        result = self._model.encode(list(texts), normalize_embeddings=False)
        return result.tolist()
