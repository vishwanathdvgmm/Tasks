# Task 02 — High-Throughput Async AI Services

Runnable FastAPI learning project demonstrating async endpoints, Pydantic v2 validation, dependency injection, SSE token streaming, SQLite async sessions, CORS, timing middleware, JSON errors, and tests.

> Inference and embeddings are deterministic mocks. Mock embeddings are for API plumbing only, not semantic search.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync --group dev
```

This creates `.venv` and installs dependencies. Generate and commit a lockfile for reproducible installs:

```bash
uv lock
uv sync --locked --group dev
```

Copy `.env.example` to `.env` (Windows PowerShell: `Copy-Item .env.example .env`; macOS/Linux: `cp .env.example .env`), then run:

```bash
uv run uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs. The development API key is `dev-secret-key`; change it before exposing the service.

## Endpoints

| Method | Path                   | Auth       | Purpose                                     |
| ------ | ---------------------- | ---------- | ------------------------------------------- |
| GET    | `/health`              | No         | Liveness                                    |
| GET    | `/ready`               | No         | SQLite readiness                            |
| GET    | `/v1/status`           | Bearer key | Mock model status                           |
| POST   | `/v1/chat/completions` | Bearer key | SSE by default; set `stream:false` for JSON |
| POST   | `/v1/embeddings`       | Bearer key | Stable 16-dimensional mock embeddings       |

## Stream tokens

```bash
curl -N http://127.0.0.1:8000/v1/chat/completions \
  -H 'Authorization: Bearer dev-secret-key' -H 'Content-Type: application/json' \
  -d '{"prompt":"Explain async Python","max_tokens":20}'
```

SSE emits a metadata event, `data: {"token":"..."}` events, and `data: [DONE]`. Events are separated by blank lines. Configure reverse proxies not to buffer SSE.

## Embeddings

```bash
curl http://127.0.0.1:8000/v1/embeddings \
  -H 'Authorization: Bearer dev-secret-key' -H 'Content-Type: application/json' \
  -d '{"input":["first sentence","second sentence"]}'
```

## Tests

```bash
uv run pytest -q
```

## Structure

```text
app/
├── config.py        # Environment settings
├── database.py      # Async SQLAlchemy engine and session dependency
├── dependencies.py  # API-key auth and per-process rate limit
├── main.py          # Routes, middleware, handlers, lifespan
├── schemas.py       # Pydantic v2 models
└── services.py      # Mock async token generator and embeddings
tests/test_api.py
pyproject.toml
uv.lock             # Create with `uv lock`, then commit
.env.example
README.md
```

## Interview notes

1. **Why asyncio?** LLM calls are I/O-bound and often wait seconds. `await` suspends the current coroutine while the event loop serves other requests. It improves concurrency, not model compute speed.
2. **SSE vs WebSockets?** SSE is one-way server-to-client over HTTP and suits token output. WebSockets are bidirectional. SSE replay requires event IDs and server-side retention if guaranteed replay is needed.
3. **Disconnects and billing?** Check `request.is_disconnected()`, propagate cancellation, and close the upstream provider stream in `finally`. Cancellation is best-effort; it cannot guarantee immediate provider cancellation or refund charges.
4. **Depends and pooling?** `Depends` separates auth, rate limits, and DB session creation from route logic. Async SQLAlchemy engine is created once and disposed during lifespan shutdown; sessions are yielded and closed per request.
5. **Event-loop blocking?** Synchronous sleeps, blocking I/O, and CPU-heavy work inside async handlers stall other requests. Use async libraries, `asyncio.to_thread()` for blocking I/O, and process pools or dedicated inference workers for CPU-bound workloads.

## Production caveats

- The limiter is in-memory, per-process, and resets on restart; use Redis/API gateway for distributed limits.
- Replace the mock model with an `httpx.AsyncClient` provider stream and ensure upstream response closure on cancellation.
- Middleware timing measures until the response object is returned, not the full SSE lifetime; add stream-duration and token telemetry.
- Add secret management, concurrency caps, timeouts, provider error mapping, metrics/tracing, migrations, and proxy streaming configuration before production.
