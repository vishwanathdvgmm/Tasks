import asyncio
from collections import defaultdict
from typing import Any

# Demo-only in-memory store. Data resets on restart and is not multi-worker safe.
_feedback: list[dict[str, Any]] = []
_usage_by_tenant: dict[str, float] = defaultdict(float)
_lock = asyncio.Lock()

async def add_usage(tenant_id: str, cost: float) -> float:
    async with _lock:
        _usage_by_tenant[tenant_id] += cost
        return _usage_by_tenant[tenant_id]

async def tenant_usage(tenant_id: str) -> float:
    async with _lock:
        return _usage_by_tenant[tenant_id]

async def add_feedback(item: dict[str, Any]) -> None:
    async with _lock:
        _feedback.append(item)

async def all_feedback() -> list[dict[str, Any]]:
    async with _lock:
        return list(_feedback)
