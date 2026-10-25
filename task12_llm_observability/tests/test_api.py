from fastapi.testclient import TestClient
from task12_observability.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_chat_returns_usage_and_trace():
    response = client.post("/chat", json={
        "message": "What is RAG?",
        "user_id": "user-test",
        "tenant_id": "tenant-test"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"]
    assert body["usage"]["prompt_tokens"] > 0
    assert body["usage"]["estimated_cost_usd"] >= 0

def test_feedback_linked_to_trace():
    response = client.post("/feedback", json={
        "trace_id": "abc123",
        "rating": "thumbs_down",
        "correction": "The answer missed a detail"
    })
    assert response.status_code == 201
    assert response.json()["trace_id"] == "abc123"

def test_feedback_requires_rating_or_correction():
    response = client.post("/feedback", json={"trace_id": "abc123"})
    assert response.status_code == 422

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "llm_requests_total" in response.text

def test_stream_endpoint():
    response = client.post("/chat/stream", json={
        "message": "Hello",
        "user_id": "user-stream",
        "tenant_id": "tenant-stream"
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert '"done": true' in response.text
