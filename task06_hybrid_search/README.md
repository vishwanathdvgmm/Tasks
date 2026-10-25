# Task 06 — Hybrid Search, Re-Ranking & Precision Retrieval

A runnable reference implementation combining PostgreSQL full-text retrieval, pgvector cosine similarity, Reciprocal Rank Fusion (RRF), and local cross-encoder reranking.

## Requirements

- Python 3.11+
- Docker Desktop (or PostgreSQL 16 with the pgvector extension)
- `uv`
- Internet access on the first run to download the local embedding and reranker models

## 1. Start PostgreSQL

```bash
docker-compose up -d
```

Wait until the database health check passes. The database is exposed on port `5433` to avoid conflicting with a local PostgreSQL instance.

## 2. Install dependencies with uv

```bash
uv sync
```

Optional: copy `.env.example` to `.env` and set `DATABASE_URL`, `EMBEDDING_MODEL`, and `RERANKER_MODEL` in your shell. The defaults work with the provided Compose file.

PowerShell:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5433/task06"
```

Git Bash:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/task06"
```

## 3. Initialize and seed

```bash
uv run task06 check
uv run task06 seed --tenant org_demo
```

The embedding model is `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). The first run downloads it. The cross-encoder model is `cross-encoder/ms-marco-MiniLM-L-6-v2`, also downloaded on first reranking.

## 4. Run searches

```bash
uv run task06 search "ERR-5034 connection timeout" --mode vector
uv run task06 search "ERR-5034 connection timeout" --mode lexical
uv run task06 search "ERR-5034 connection timeout" --mode hybrid
uv run task06 search "SKU XJ-204" --mode hybrid --top-k 5
```

- `vector`: dense retrieval ordered by cosine distance.
- `lexical`: PostgreSQL `tsvector` / `websearch_to_tsquery` and `ts_rank_cd`.
- `hybrid`: top 50 candidates from both retrieval paths, RRF fusion with `k=60`, then cross-encoder reranking to top 5.

PostgreSQL's built-in full-text rank is a lexical baseline, not BM25. To use true BM25, add an extension such as ParadeDB pg_search or a dedicated BM25 service and keep the same RRF interface.

## 5. Benchmark

```bash
uv run task06 benchmark --tenant org_demo
```

The benchmark reports mean `precision@5`, `recall@5`, and `MRR@5` over the included labeled query set. These are small demo results, not general claims about production performance. Expand the query set and relevance judgments before drawing conclusions.

## 6. Tests

```bash
uv run pytest
uv run ruff check .
```

Unit tests cover RRF ranking math, deduplication, and retrieval metrics. They do not require PostgreSQL or model downloads. The end-to-end CLI commands do require the database and local models.

## Project structure

```text
task06_hybrid_search/
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── README.md
├── src/task06/
│   ├── cli.py
│   ├── config.py
│   ├── db.py
│   ├── embeddings.py
│   ├── models.py
│   ├── seed.py
│   ├── retrieval.py
│   ├── rrf.py
│   ├── reranker.py
│   ├── metrics.py
│   └── benchmark.py
└── tests/
    ├── test_rrf.py
    └── test_metrics.py
```

## Important design notes

1. **Two-stage retrieval:** retrieval builds a high-recall candidate pool; reranking spends more compute on a much smaller set.
2. **RRF:** `score(d) = Σ 1 / (k + rank(d))`, using one-based ranks and `k=60`.
3. **Tenant isolation:** every retrieval query filters by `tenant_id`. In production, also enforce tenant isolation with database roles or row-level security.
4. **Reranking cost:** cross-encoder inference can be slow on CPU; model latency depends on hardware, batch size, and candidate count. Do not assume a fixed 50 ms latency.
5. **Evaluation:** the demo qrels are intentionally small. Production evaluation needs a representative query set, human-judged relevance, and latency measurements.
