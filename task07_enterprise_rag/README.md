# Task 07 — Enterprise Retrieval-Augmented Generation (RAG)

A modular, runnable RAG assignment demonstrating query transformation, hybrid retrieval, context assembly, grounded generation, citation validation, and low-relevance fallback. The default provider is deterministic and requires no API key, so the project can be run and tested locally.

> Engineering note: this is a teaching/demo implementation, not a claim that hallucinations can be mathematically eliminated. Prompts and citation checks reduce risk; production systems also need real embeddings, calibrated retrieval, claim-level entailment verification, authorization filtering, observability, and adversarial testing.

## Architecture

1. **Request validation** — Pydantic limits question length and top-k.
2. **Multi-query expansion** — produces up to three query formulations.
3. **HyDE** — creates a hypothetical-document-style search representation. The local mock generates query-term text; swap in an LLM provider for real hypothetical answers.
4. **Hybrid retrieval** — combines a BM25-inspired lexical score with a deterministic token-vector cosine score. This keeps the demo dependency-free, but is not a substitute for learned dense embeddings.
5. **Re-ranking and threshold** — deterministic demo reranker plus configurable relevance threshold.
6. **Context assembly** — wraps each chunk in explicit source boundaries and includes chunk ID, filename, page, and metadata.
7. **Grounded generation** — extracts supported sentences and attaches source citations.
8. **Citation validation** — verifies each citation references an accepted chunk, correct page, and exact source quote.
9. **Fallback** — answers “I don't know based on the available documents” when no evidence clears the threshold or citation validation fails.

## Requirements

- Python 3.12+
- `uv`
- Optional: PostgreSQL with the `vector` extension for the production persistence exercise

## Setup with uv

```bash
uv sync --extra test
```

## Run tests

```bash
uv run pytest
```

## Run the CLI demo

```bash
uv run task07 demo
uv run task07 ask "How quickly must an incident be acknowledged?"
```

## Run the API

```bash
uv run uvicorn task07_rag.api:app --reload --app-dir src
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the requirements for remote access?","top_k":5,"multi_query":true,"hyde":true}'
```

## Configuration

Copy `.env.example` as a reference. Current settings are read from environment variables:

- `RAG_SCORE_THRESHOLD` — minimum retrieval score accepted for context, default `0.18`.
- `RAG_TOP_K` — documented default top-k, default `5`.
- `RAG_BACKEND` — defaults to `memory`.
- `DATABASE_URL` — optional PostgreSQL connection string for the next integration step.

The current runnable path uses the memory corpus so the assignment can be demonstrated without external services. `sql/schema.sql` supplies a PostgreSQL schema using `pgvector`, generated `tsvector` full-text search, tenant ID, and HNSW index. The persistence adapter and real embedding provider are explicit production extension points rather than falsely represented as active integrations.

## Example questions

- `What are the requirements for remote access?`
- `How quickly must an incident be acknowledged?`
- `When can full-time employees request learning reimbursement?`
- `What must happen before production changes?`
- `What is the company's moon base address?` (should fall back to “I don't know”)

## Submission checklist

- [x] Query transformation: three variations and HyDE-shaped retrieval query
- [x] Hybrid lexical + dense-style scoring
- [x] Re-ranking stage
- [x] Source-delimited context with filenames, pages, and metadata
- [x] Strict grounded system prompt
- [x] Citation records mapped to chunk IDs and page numbers
- [x] Citation validation against retrieved text
- [x] Low-relevance fallback
- [x] FastAPI endpoints and CLI
- [x] Tests for API, citations, query expansion, and fallback
- [x] PostgreSQL/pgvector schema for production extension

## Interview talking points

**HyDE:** a model drafts a hypothetical relevant passage, embeds it, and uses that representation to retrieve real passages. It can improve recall but can also introduce misleading terms, so retrieved evidence—not the hypothetical passage—must ground the final answer.

**Lost in the Middle:** models may use evidence less reliably when it appears in the middle of a long context. Keep the strongest evidence near the beginning, consider placing a second high-value chunk near the end, and compress irrelevant text.

**Can hallucinations be mathematically eliminated?** No—not with prompting and temperature alone. Use source-constrained generation, structured citations, exact provenance validation, claim-level entailment checks, abstention thresholds, and human review for high-impact use cases.

**Naive vs modular/agentic RAG:** naive RAG retrieves once and generates. Modular RAG can rewrite queries, combine retrievers, rerank, assess sufficiency, retry, and verify claims. Agentic orchestration adds model-directed decisions but also raises latency and operational complexity.

**Contextual compression:** extract only query-relevant sentences from retrieved chunks to reduce token use and distractors. Preserve original chunk IDs and offsets so compressed evidence remains auditable.

## Production gaps to explain honestly

This is a robust assignment scaffold, not a fully production-certified system. Replace the mock generator and token-vector stand-in with an actual LLM and embedding model; connect `sql/schema.sql` to a tenant-filtered PostgreSQL repository; use a trained cross-encoder; and add claim-level NLI/entailment evaluation, authentication, rate limiting, telemetry, evaluation datasets, and load tests before deployment.
