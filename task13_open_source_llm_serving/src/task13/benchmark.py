import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any
from .client import OpenAICompatibleClient

async def run_benchmark(
    client: OpenAICompatibleClient,
    model: str,
    prompt: str,
    requests: int = 10,
    concurrency: int = 2,
    max_tokens: int = 128,
) -> dict[str, Any]:
    if requests < 1 or concurrency < 1:
        raise ValueError("requests and concurrency must be >= 1")
    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict[str, Any]] = []

    async def one(index: int) -> None:
        async with semaphore:
            start = time.perf_counter()
            try:
                data = await client.chat(model, prompt, max_tokens=max_tokens)
                elapsed = time.perf_counter() - start
                usage = data.get("usage") or {}
                completion_tokens = usage.get("completion_tokens")
                if completion_tokens is None:
                    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                    completion_tokens = len(content.split())
                results.append({
                    "request": index,
                    "ok": True,
                    "latency_seconds": elapsed,
                    "completion_tokens": int(completion_tokens),
                    "tokens_per_second": float(completion_tokens) / elapsed if elapsed else 0.0,
                })
            except Exception as exc:
                results.append({"request": index, "ok": False, "error": str(exc)})

    started = time.perf_counter()
    await asyncio.gather(*(one(i + 1) for i in range(requests)))
    wall = time.perf_counter() - started
    successes = [r for r in results if r["ok"]]
    latencies = [r["latency_seconds"] for r in successes]
    total_tokens = sum(r["completion_tokens"] for r in successes)
    report = {
        "model": model,
        "requests": requests,
        "concurrency": concurrency,
        "successful_requests": len(successes),
        "failed_requests": requests - len(successes),
        "wall_seconds": round(wall, 4),
        "throughput_tokens_per_second": round(total_tokens / wall, 3) if wall else 0,
        "mean_latency_seconds": round(statistics.mean(latencies), 4) if latencies else None,
        "p95_latency_seconds": round(sorted(latencies)[min(len(latencies)-1, int(0.95 * len(latencies)))] , 4) if latencies else None,
        "total_completion_tokens": total_tokens,
        "results": sorted(results, key=lambda r: r["request"]),
    }
    return report

def save_report(report: dict[str, Any], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
