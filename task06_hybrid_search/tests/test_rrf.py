from task06.models import SearchResult
from task06.rrf import reciprocal_rank_fusion

def item(doc_id):
    return SearchResult(doc_id, doc_id, "content", 1.0, "test")

def test_rrf_promotes_documents_present_in_multiple_lists():
    result = reciprocal_rank_fusion([[item("a"), item("b")], [item("b"), item("a")]])
    assert result[0].external_id == "a" or result[0].external_id == "b"
    scores = {r.external_id: r.score for r in result}
    assert scores["a"] == scores["b"]

def test_rrf_uses_one_based_ranks_and_expected_formula():
    result = reciprocal_rank_fusion([[item("a"), item("b")]], k=60)
    scores = {r.external_id: r.score for r in result}
    assert abs(scores["a"] - 1 / 61) < 1e-12
    assert abs(scores["b"] - 1 / 62) < 1e-12

def test_rrf_deduplicates_document_within_one_list():
    result = reciprocal_rank_fusion([[item("a"), item("a")]], k=60)
    assert len(result) == 1

def test_rrf_rejects_invalid_k():
    import pytest
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([], k=0)
