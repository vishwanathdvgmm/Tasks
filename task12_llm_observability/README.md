# Task 12 — LLM Observability, Distributed Tracing & Token Cost Tracking

A runnable, offline-first FastAPI starter demonstrating:

- OpenTelemetry root/child spans for a multi-step RAG-shaped pipeline
- Token accounting and configurable estimated cost
- Streaming Server-Sent Events (SSE) with TTFT and inter-token latency (ITL) metrics
- Tenant/user attribution and a basic tenant spend ceiling
- User feedback associated with trace IDs
- Prometheus `/metrics` endpoint
- Automated tests and GitHub Actions CI

## Quick start (Python 3.11+)

```bash
python -m venv .venv
# Windows Git Bash:
source .venv/Scripts/activate
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn task12_observability.main:app --reload
```

Open http://127.0.0.1:8000/docs. Health: `GET /health`.

## Test

```bash
pytest -q
```

## Try the API

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain hybrid retrieval","user_id":"u1","tenant_id":"org_demo"}'
```

Streaming endpoint:

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","user_id":"u1","tenant_id":"org_demo"}'
```

Submit feedback (use a trace ID returned from `/chat`):

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"trace_id":"YOUR_TRACE_ID","rating":"thumbs_down","correction":"Missing citations"}'
```

Prometheus metrics: `GET /metrics`. Tenant usage: `GET /usage/org_demo`.

## Architecture

`POST /chat` -> root trace -> query rewrite -> retrieval -> reranker -> prompt construction -> model generation -> usage/cost accounting. `/chat/stream` demonstrates TTFT/ITL measurement. `/feedback` stores feedback with a trace ID.

## Important scope notes

This is an **educational starter**, not yet a production deployment:

- LLM and retrieval steps are deterministic demo placeholders. Replace them with the real clients and functions from your Tasks 07–11 repository.
- Token counts use a character-based approximation; use provider-reported usage in production.
- Pricing values are illustrative, configurable estimates. Confirm current pricing for your chosen model.
- The OpenTelemetry SDK writes spans to the console. To send traces to Langfuse, Phoenix, or an OTLP collector, configure the matching exporter/SDK integration and secrets.
- Feedback and tenant spend are held in process memory and reset on restart. Use durable storage and atomic Redis budget accounting for production.
- The demo trace ID returned by `/chat` identifies the active OpenTelemetry trace, but a trace viewer lookup API is not implemented.
- Do not log raw prompts or retrieved content without privacy controls. Add authentication/authorization before exposing usage, feedback, or trace data.

## Production integration checklist

1. Replace demo retrieval, reranking and generation with the existing Tasks 07–11 services.
2. Use provider token usage and model-specific pricing.
3. Configure OTLP/Langfuse/Phoenix exporter and verify traces in its UI.
4. Store feedback and usage in PostgreSQL; use Redis atomic counters/limits for tenant budgets.
5. Add authentication, tenant authorization, retention rules, redaction, and rate limits.
6. Add integration tests against test instances of Redis and your tracing backend.
