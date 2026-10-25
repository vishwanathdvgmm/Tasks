import asyncio
import json
import pytest
from task09.registry import ToolRegistry

@pytest.mark.asyncio
async def test_independent_tools_can_be_gathered():
    registry = ToolRegistry()
    results = await asyncio.gather(
        registry.execute("weather", {"city": "Bengaluru"}),
        registry.execute("weather", {"city": "London"}),
    )
    parsed = [json.loads(r) for r in results]
    assert all(item["ok"] for item in parsed)
    assert parsed[0]["result"]["city"] == "Bengaluru"
    assert parsed[1]["result"]["city"] == "London"
