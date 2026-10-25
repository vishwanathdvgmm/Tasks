"""Deterministic demo embeddings; replace with a real embedding provider for semantic quality.

This intentionally avoids API keys so the assignment runs locally. It is NOT a semantic
embedding model and should only be used to exercise storage, indexing, and retrieval paths.
"""
import hashlib
import numpy as np

def demo_embedding(text: str, dimensions: int = 1536) -> list[float]:
    """Create a stable, normalized vector from text using repeated SHA-256 blocks."""
    if dimensions < 1:
        raise ValueError("dimensions must be positive")
    raw = text.encode("utf-8")
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        digest = hashlib.sha256(counter.to_bytes(4, "big") + raw).digest()
        for offset in range(0, len(digest), 4):
            integer = int.from_bytes(digest[offset:offset + 4], "big")
            values.append((integer / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(values) == dimensions:
                break
        counter += 1
    vector = np.asarray(values, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    return vector.tolist()
