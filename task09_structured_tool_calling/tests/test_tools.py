import json
import pytest
from task09.registry import ToolRegistry

@pytest.mark.asyncio
async def test_calculator_tool():
    result = json.loads(await ToolRegistry().execute("calculator", {"expression": "19 * 23"}))
    assert result["ok"] is True
    assert result["result"]["result"] == 437

@pytest.mark.asyncio
async def test_rejects_code_execution_expression():
    result = json.loads(await ToolRegistry().execute(
        "calculator", {"expression": "__import__('os').system('whoami')"}
    ))
    assert result["ok"] is False

@pytest.mark.asyncio
async def test_unknown_tool_is_rejected():
    result = json.loads(await ToolRegistry().execute("shell", {"command": "whoami"}))
    assert result["ok"] is False

@pytest.mark.asyncio
async def test_sql_tool_is_allow_listed():
    result = json.loads(await ToolRegistry().execute("safe_sql", {"query_name": "demo_users"}))
    assert result["ok"] is True
    assert len(result["result"]["rows"]) == 2
