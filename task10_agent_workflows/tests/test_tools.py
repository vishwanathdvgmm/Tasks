import pytest
from task10_agent_workflows.tools import safe_calculate, retrieve, execute_tool

def test_safe_calculator():
    assert safe_calculate("12 * 7") == 84
    assert safe_calculate("(8 + 2) / 5") == 2

def test_calculator_rejects_calls():
    with pytest.raises((ValueError, SyntaxError)):
        safe_calculate("__import__('os').system('echo unsafe')")

def test_retrieve_returns_evidence():
    assert retrieve("state graph checkpoint")

def test_tool_allowlist():
    with pytest.raises(ValueError):
        execute_tool("shell", "rm -rf /")
