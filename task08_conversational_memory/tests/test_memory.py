from app.memory import MemoryManager
from app.token_budget import TokenBudget

def sample_messages(n=10):
    out = []
    for i in range(n):
        out.extend([{"role":"user","content":f"Question {i}"},{"role":"assistant","content":f"Answer {i}"}])
    return out

def test_sliding_window_keeps_recent_messages():
    manager = MemoryManager(TokenBudget(max_tokens=1000))
    result = manager.sliding_window(sample_messages(), max_turns=2)
    assert len(result) == 4
    assert result[-1]["content"] == "Answer 9"

def test_summary_buffer_returns_summary_and_recent_messages():
    manager = MemoryManager(TokenBudget(max_tokens=1000))
    summary, recent = manager.summary_buffer(sample_messages(), max_recent_messages=4)
    assert summary
    assert len(recent) == 4

def test_entity_memory_extracts_and_preserves_entities():
    manager = MemoryManager(TokenBudget(max_tokens=1000))
    messages = [{"role":"user","content":"I am comparing Dezinet Teams plans."}]
    entities, recent = manager.entity_memory(messages)
    assert "Dezinet Teams" in entities
    assert recent == messages

def test_build_context_strategy():
    manager = MemoryManager(TokenBudget(max_tokens=1000))
    assert manager.build_context("sliding_window", sample_messages())["messages"]
