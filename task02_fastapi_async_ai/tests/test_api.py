from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import _buckets

client = TestClient(app)
HEADERS = {"Authorization": "Bearer dev-secret-key"}

def setup_function():
    _buckets.clear()

def test_health_and_readiness():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").status_code == 200

def test_requires_api_key():
    assert client.post("/v1/embeddings", json={"input":"hello"}).status_code == 401

def test_rejects_invalid_request():
    response = client.post("/v1/chat/completions", headers=HEADERS,
                           json={"prompt":"   ","max_tokens":10})
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"

def test_embedding_shape_and_determinism():
    response = client.post("/v1/embeddings", headers=HEADERS,
                           json={"input":["hello","world"]})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2 and len(data[0]["embedding"]) == 16
    again = client.post("/v1/embeddings", headers=HEADERS, json={"input":"hello"})
    assert data[0]["embedding"] == again.json()["data"][0]["embedding"]

def test_sse_stream():
    with client.stream("POST", "/v1/chat/completions", headers=HEADERS,
                       json={"prompt":"hello async world","max_tokens":10}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
        assert "event: metadata" in body and '"token": "Mock' in body and "[DONE]" in body

def test_non_streaming_completion():
    response = client.post("/v1/chat/completions", headers=HEADERS,
                           json={"prompt":"hello","stream":False})
    assert response.status_code == 200
    assert "Mock response" in response.json()["choices"][0]["message"]["content"]
