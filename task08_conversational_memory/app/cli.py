import argparse
import asyncio
from redis.asyncio import Redis
from app.config import settings
from app.memory import MemoryManager
from app.token_budget import TokenBudget

async def check():
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
        print("Redis connection OK")
    finally:
        await client.aclose()

def benchmark():
    import time
    sample = []
    for i in range(40):
        sample += [
            {"role": "user", "content": f"I am discussing Project Atlas feature {i} and need a cost estimate."},
            {"role": "assistant", "content": f"Project Atlas feature {i} has several implementation considerations."},
        ]
    manager = MemoryManager(TokenBudget(max_tokens=1000))
    for strategy in ("sliding_window", "summary_buffer", "entity"):
        start = time.perf_counter()
        context = manager.build_context(strategy, sample, "Earlier discussion covered project goals.")
        elapsed = (time.perf_counter() - start) * 1000
        count = manager.budget.count_messages(context["messages"])
        print(f"{strategy:16} messages={len(context['messages']):3} tokens={count:4} elapsed_ms={elapsed:.2f}")

def main():
    parser = argparse.ArgumentParser(prog="task08")
    parser.add_argument("command", choices=["check", "benchmark"])
    args = parser.parse_args()
    if args.command == "check":
        asyncio.run(check())
    elif args.command == "benchmark":
        benchmark()

if __name__ == "__main__":
    main()
