"""Numerically safe vector similarity and distance metrics."""
from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike, NDArray

def _vector(value: ArrayLike, name: str) -> NDArray[np.float64]:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional vector")
    if result.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite numbers")
    return result

def _pair(a: ArrayLike, b: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    x, y = _vector(a, "a"), _vector(b, "b")
    if x.shape != y.shape:
        raise ValueError("vectors must have the same dimensions")
    return x, y

def dot_product(a: ArrayLike, b: ArrayLike) -> float:
    """Return the inner product; vector magnitudes affect the result."""
    x, y = _pair(a, b)
    return float(np.dot(x, y))

def cosine_similarity(a: ArrayLike, b: ArrayLike) -> float:
    """Return cosine similarity in [-1, 1]; undefined for zero vectors."""
    x, y = _pair(a, b)
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denominator == 0:
        raise ValueError("cosine similarity is undefined for zero vectors")
    return float(np.dot(x, y) / denominator)

def euclidean_distance(a: ArrayLike, b: ArrayLike) -> float:
    """Return L2 distance; smaller means closer."""
    x, y = _pair(a, b)
    return float(np.linalg.norm(x - y))

def l2_normalize(vector: ArrayLike) -> NDArray[np.float64]:
    """Return a unit-length copy; zero vectors are rejected."""
    x = _vector(vector, "vector")
    norm = float(np.linalg.norm(x))
    if norm == 0:
        raise ValueError("cannot normalize a zero vector")
    return x / norm
