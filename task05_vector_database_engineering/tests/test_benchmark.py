import pytest
from task05_vector_db.benchmark import benchmark_search

def test_benchmark_returns_expected_metrics():
    result = benchmark_search(lambda: sum(range(20)), iterations=5)
    assert result["iterations"] == 5
    assert result["mean_ms"] >= 0
    assert result["p50_ms"] >= 0
    assert result["p95_ms"] >= 0
    assert result["qps"] > 0

def test_benchmark_rejects_zero_iterations():
    with pytest.raises(ValueError):
        benchmark_search(lambda: None, iterations=0)
