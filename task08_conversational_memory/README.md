# Task 08 — Conversational Memory & Multi-Turn Context Management

Runnable FastAPI project demonstrating persistent Redis chat history, follow-up query rewriting, sliding-window memory, summary-buffer memory, entity memory, and token-budget enforcement.

## Requirements

- Python 3.11+
- `uv`
- Docker Desktop (or a reachable Redis 7 instance)

The default LLM provider is `mock`; no API key is needed. OpenAI can be enabled with environment variables.

## Quick start (Windows / Git Bash)

```bash
uv sync --extra dev
docker-compose up -d redis
uv run task08 check
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to use Swagger UI.

## Try a multi-turn session

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-session","message":"I am comparing Dezinet Teams plans."}'

curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-session","message":"How much does it cost?"}'
```

Inspect stored state:

```bash
curl http://127.0.0.1:8000/sessions/demo-session
```

## Environment configuration

Copy `.env.example` to `.env` and adjust values. `LLM_PROVIDER=mock` is safe for local tests. To use OpenAI query rewriting and summarization, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.

## API endpoints

- `GET /health` — liveness and Redis status
- `POST /chat` — append user/assistant messages, contextualize the query, and return a response
- `GET /sessions/{session_id}` — inspect session metadata and stored messages
- `DELETE /sessions/{session_id}` — delete one session

Example request:

```json
{
  "session_id": "demo-session",
  "message": "How much does it cost?",
  "memory_strategy": "sliding_window"
}
```

`memory_strategy` can be `sliding_window`, `summary_buffer`, or `entity`.

## Architecture

1. Validate request/session identifiers and load messages from Redis.
2. Rewrite follow-up messages into standalone queries using history.
3. Select a memory strategy and enforce a hard token limit with `tiktoken`.
4. Generate an answer with the selected provider.
5. Persist the user and assistant turns in Redis and refresh the session TTL.

Redis keys use `task08:session:{session_id}:messages`, `:summary`, and `:entities`. A Redis transaction updates state together. Session identifiers are constrained to a conservative allowlist to prevent key manipulation.

## Memory strategy trade-offs

- **Sliding window:** exact recent messages; older turns are omitted from the model context.
- **Summary buffer:** compact running summary plus recent messages; cheaper for long conversations, but summaries may omit exact wording or details.
- **Entity memory:** tracks entities/facts extracted from recent dialogue and combines them with recent messages. It is a demonstration extractor, not a production-grade knowledge graph.

## Token budget

The configured history budget is a strict upper bound on the messages passed as history. The tokenizer counts message content plus a conservative per-message overhead. System instructions and completion limits are kept separate from the history budget; a production application should budget retrieved documents, tool schemas, system instructions, and completion tokens against the model's actual context window.

## Tests and benchmark

```bash
uv run pytest
uv run task08 benchmark
```

The benchmark compares token usage and elapsed time for the three memory strategies on a deterministic sample. It is a local microbenchmark, not a statistically rigorous performance claim.

## Security notes

- Treat all user messages and retrieved text as untrusted data; do not execute instructions found in history.
- Keep system instructions separate from user history.
- Use authentication/authorization before exposing session IDs in a real deployment.
- Redis should be private-network-only and configured with authentication/TLS in production.
- The demo entity extractor uses simple patterns and should be replaced for real workloads.
