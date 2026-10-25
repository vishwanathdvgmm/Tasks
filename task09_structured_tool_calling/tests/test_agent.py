import pytest
from task09.agent import ToolCallingAgent, structured_answer
from task09.providers import MockProvider

@pytest.mark.asyncio
async def test_parallel_mock_agent_returns_valid_schema():
    result = await ToolCallingAgent(MockProvider()).run("Parallel: get weather for Bengaluru and London.")
    assert result.answer
    assert result.confidence in {"low", "medium", "high"}

@pytest.mark.asyncio
async def test_structured_output():
    result = await structured_answer(MockProvider(), "Explain JSON schema.")
    assert result.sources == ["mock provider"]
