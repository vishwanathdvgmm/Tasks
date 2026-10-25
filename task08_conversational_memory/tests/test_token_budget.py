from app.token_budget import TokenBudget

def test_trim_enforces_budget():
    budget = TokenBudget(max_tokens=35)
    messages = [{"role": "user", "content": "word " * 100}, {"role": "assistant", "content": "short"}]
    result = budget.trim(messages)
    assert budget.count_messages(result) <= 35

def test_empty_history():
    budget = TokenBudget(max_tokens=10)
    assert budget.trim([]) == []
