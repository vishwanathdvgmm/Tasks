import pytest
from task06.metrics import precision_at_k, recall_at_k, reciprocal_rank_at_k, evaluate

def test_mrr_uses_first_relevant_rank():
    assert reciprocal_rank_at_k(["x", "b", "a"], {"a", "b"}, 5) == 0.5

def test_mrr_zero_when_no_relevant_hit():
    assert reciprocal_rank_at_k(["x", "y"], {"a"}, 5) == 0.0

def test_recall_and_precision():
    assert recall_at_k(["a", "x"], {"a", "b"}, 2) == 0.5
    assert precision_at_k(["a", "x"], {"a"}, 2) == 0.5

def test_precision_requires_positive_k():
    with pytest.raises(ValueError):
        precision_at_k([], set(), 0)

def test_evaluate_checks_query_counts():
    with pytest.raises(ValueError):
        evaluate({"sys": [["a"]]}, [], 5)
