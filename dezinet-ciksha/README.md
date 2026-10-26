# Dezinet CIKSHA — AI Knowledge Engine & Enterprise Search

A containerized capstone starter that combines document ingestion, hybrid retrieval, grounded RAG, SSE streaming, Redis conversation memory, tenant-scoped retrieval, and observability hooks.

## Architecture

- **Frontend:** React + Vite
- **API:** FastAPI
- **Storage:** PostgreSQL + pgvector
- **Cache/session memory:** Redis
- **LLM + embeddings:** Ollama (`qwen2.5:3b` and `nomic-embed-text` by default)
- **Evaluation:** RAGAS-ready evaluation dataset and benchmark script
- **Observability:** optional Langfuse environment configuration; API includes structured request timing and token placeholders

> This is a runnable portfolio MVP, not a claim of production certification. Before production, add enterprise identity integration, secret management, formal threat modeling, robust migrations, rate limiting, and load testing.

## Quick start

Requirements: Docker Desktop / Docker Engine with Compose, 8 GB+ RAM recommended.

```bash
cp .env.example .env
docker-compose up --build -d
docker-compose exec ollama ollama pull qwen2.5:3b
docker-compose exec ollama ollama pull nomic-embed-text
```

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The first model download can take several minutes. Ollama model files need disk space.

## Basic workflow

1. Open the frontend and enter a tenant ID (demo default: `dezinet-demo`).
2. Upload a PDF, Markdown, or HTML file.
3. Ask a question about the uploaded content.
4. Observe streamed answer text and source citations.

API examples:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/documents \
  -H 'X-Tenant-ID: dezinet-demo' \
  -F 'file=@README.md'
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: dezinet-demo' \
  -d '{"session_id":"demo-session","question":"What does this project do?"}'
```

## Endpoints

- `GET /health` — readiness checks
- `POST /api/documents` — parse, chunk, embed, and store a document
- `POST /api/search` — hybrid retrieval (dense + lexical) with reciprocal-rank fusion
- `POST /api/chat/stream` — SSE response stream with citations
- `GET /api/sessions/{session_id}/history` — tenant-scoped Redis history
- `GET /docs` — OpenAPI/Swagger UI

## Security notes

- Every document/chunk is associated with `tenant_id`.
- API requests use `X-Tenant-ID` for this demonstration. **Do not treat this header as authentication**: production must derive tenant identity from a verified identity token or server-side session.
- Database access uses tenant predicates. Add PostgreSQL RLS and set a transaction-scoped tenant identity before production use.
- Uploaded files are size-limited and stored temporarily. Add malware scanning and stricter content validation for untrusted uploads.
- Retrieved content is treated as untrusted data; the system prompt instructs the model not to follow instructions found inside documents.
- Never expose `.env`, credentials, internal prompts, or secrets to the frontend.

## Evaluation

Install local evaluation dependencies if desired:

```bash
pip install -r requirements-eval.txt
python scripts/benchmark.py
```

The benchmark script measures retrieval MRR@5 and Hit Rate@5 against a small editable fixture. RAGAS faithfulness requires a configured LLM and a curated dataset; do not claim >90% without running a statistically meaningful evaluation. TTFT <800 ms is a target, not guaranteed; local model cold starts may exceed it.

## Troubleshooting

- `ollama` model unavailable: run the `ollama pull` commands above.
- PostgreSQL not ready: `docker compose ps` and `docker compose logs db`.
- Embedding dimension mismatch: the schema uses 768 dimensions for `nomic-embed-text`. If you change embedding models, update the vector dimension and recreate the database volume.
- Reset all local data: `docker compose down -v` (destructive; deletes stored documents and sessions).

## Suggested next steps

1. Replace demo tenant header with JWT/OIDC authentication.
2. Add RLS policies and migration tooling (Alembic).
3. Add a background ingestion queue and object storage for raw files.
4. Add reranker model serving and calibrated RAGAS evaluation.
5. Add CI tests, dependency scanning, image scanning, and deployment workflows.
