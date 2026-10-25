from __future__ import annotations

from pathlib import Path
from statistics import mean
from time import perf_counter

from .pipeline import STRATEGIES, ingest

def benchmark(path: Path, max_tokens: int = 500, overlap_tokens: int = 50,
              encoding_name: str = "cl100k_base", ocr: bool = False) -> dict:
    report = {
        "input_path": str(path),
        "tokenizer": encoding_name,
        "max_tokens": max_tokens,
        "overlap_tokens": overlap_tokens,
        "strategies": {},
    }
    for strategy in STRATEGIES:
        start = perf_counter()
        chunks = ingest(path, strategy, max_tokens, overlap_tokens, encoding_name, ocr)
        elapsed = perf_counter() - start
        counts = [c.token_count for c in chunks]
        report["strategies"][strategy] = {
            "chunk_count": len(chunks),
            "total_tokens": sum(counts),
            "mean_tokens": round(mean(counts), 2) if counts else 0,
            "max_tokens_observed": max(counts, default=0),
            "min_tokens_observed": min(counts, default=0),
            "elapsed_seconds": round(elapsed, 4),
        }
    return report
