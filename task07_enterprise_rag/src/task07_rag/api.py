from fastapi import FastAPI, HTTPException
from .models import AnswerRequest, AnswerResponse
from .pipeline import RAGPipeline

app = FastAPI(title="Task 07 — Enterprise RAG API", version="0.1.0", description="Modular RAG demo with hybrid retrieval, grounded answers, and auditable citations.")
pipeline = RAGPipeline()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "backend": "memory", "provider": "mock"}

@app.post("/answer", response_model=AnswerResponse)
def answer(request: AnswerRequest) -> AnswerResponse:
    try:
        return pipeline.answer(request)
    except Exception as exc:
        # Do not expose internal exception details to API clients.
        raise HTTPException(status_code=500, detail="RAG pipeline failed. Check application logs.") from exc
