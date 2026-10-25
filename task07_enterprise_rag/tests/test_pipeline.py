from fastapi.testclient import TestClient
from task07_rag.api import app
from task07_rag.models import AnswerRequest
from task07_rag.pipeline import RAGPipeline

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_answer_returns_valid_citations():
    result = RAGPipeline().answer(AnswerRequest(question="What are the requirements for remote access?"))
    assert result.answer
    assert result.citations
    retrieved = set(result.retrieved_chunk_ids)
    for citation in result.citations:
        assert citation.chunk_id in retrieved
        assert citation.page_number >= 1
        assert citation.source_filename.endswith(".pdf")

def test_unknown_question_uses_fallback():
    result = RAGPipeline(score_threshold=0.99).answer(AnswerRequest(question="What is the company moon base address?"))
    assert result.fallback_used is True
    assert "I don't know" in result.answer
    assert result.citations == []

def test_multi_query_generates_three_variants():
    result = RAGPipeline().answer(AnswerRequest(question="How does learning reimbursement work?"))
    assert 1 <= len(result.query_variations) <= 3
    assert "multi_query_expansion" in result.pipeline

def test_api_answer_contract():
    response = client.post("/answer", json={"question": "How quickly must an incident be acknowledged?"})
    assert response.status_code == 200
    body = response.json()
    assert body["question"]
    assert isinstance(body["citations"], list)
    assert "citation_validation" in body["pipeline"]
