from __future__ import annotations

from time import perf_counter
from typing import Callable

def benchmark_search(search_fn: Callable[[], object], iterations: int = 50) -> dict[str, float]:
    """Return latency percentiles and throughput for a callable search operation."""
    if iterations < 1:
        raise ValueError("iterations must be positive")
    durations = []
    for _ in range(iterations):
        started = perf_counter()
        search_fn()
        durations.append((perf_counter() - started) * 1000)
    ordered = sorted(durations)
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    total_seconds = sum(durations) / 1000
    return {
        "iterations": float(iterations),
        "mean_ms": sum(durations) / len(durations),
        "p50_ms": ordered[len(ordered) // 2],
        "p95_ms": ordered[p95_index],
        "qps": iterations / total_seconds if total_seconds else float("inf"),
    }
