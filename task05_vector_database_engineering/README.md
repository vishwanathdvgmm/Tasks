# Task 05 — Production Vector Database Engineering

A runnable engineering lab for PostgreSQL + pgvector and embedded ChromaDB. It includes a Dockerized PostgreSQL service, a `vector(1536)` schema, tenant-scoped hybrid search, HNSW/IVFFlat index creation, and a latency/QPS benchmark.

## Important note about embeddings

The project uses a **deterministic demo vector generator** so the workflow runs without API keys. It is suitable for testing persistence, dimensions, indexes, tenant filtering, and benchmarks, but it is **not a semantic embedding model**. For meaningful retrieval quality, replace `demo_embedding()` with the same production embedding model used for your documents and queries.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop / Docker Engine

## 1. Install dependencies

```bash
uv sync --extra dev
```

Optionally copy `.env.example` to `.env` and adjust the connection string.

## 2. Start PostgreSQL with pgvector

```bash
docker-compose up -d
docker-compose ps
```

The container initializes `sql/001_init.sql` on its **first** database-volume creation. If you change the initialization SQL later, apply it manually or reset the disposable volume with `docker compose down -v` (this deletes the local database data).

Check connectivity:

```bash
uv run task05 check
```

## 3. Seed and query PostgreSQL

```bash
uv run task05 seed --tenant org_demo
uv run task05 search "graph based vector index" --tenant org_demo --limit 3
```

Try the distance operators:

```bash
uv run task05 search "vector index" --metric cosine
uv run task05 search "vector index" --metric l2
uv run task05 search "vector index" --metric inner_product
```

pgvector operator meanings:

- `<=>`: cosine distance (smaller is closer)
- `<->`: Euclidean/L2 distance (smaller is closer)
- `<#>`: negative inner product (smaller is better for maximum inner product)

## 4. Create and tune ANN indexes

HNSW (graph-based; higher build time and memory, generally strong recall):

```bash
uv run task05 index hnsw
```

Uses `m = 16` and `ef_construction = 64`; search effort can be tuned in a session with SQL:

```sql
SET hnsw.ef_search = 40;
```

IVFFlat (centroid/list partitioning; needs representative existing data to train effectively):

```bash
uv run task05 index ivfflat --lists 10
```

Tune probes in a session:

```sql
SET ivfflat.probes = 5;
```

For a fair comparison, seed a substantially larger representative dataset, run the same queries, and measure recall against exact search as well as latency/QPS. Four sample records are only enough to validate the code path, not to draw performance conclusions.

## 5. Benchmark search latency and throughput

```bash
uv run task05 benchmark --tenant org_demo --iterations 30
```

Reports mean, p50, p95 latency (ms) and approximate single-process QPS. Run multiple iterations and compare HNSW and IVFFlat with different search-effort settings. Benchmarking with the tiny sample dataset is a smoke test, not a production benchmark.

## 6. Run ChromaDB locally

ChromaDB is embedded and persists data to `./.chroma`:

```bash
uv run task05 chroma-seed --tenant org_demo
uv run task05 chroma-search "graph based vector index" --tenant org_demo
```

The Chroma search includes `where={"tenant_id": ...}`. The PostgreSQL query similarly places `tenant_id = %s` in the SQL query. Do not rely on caller-supplied tenant IDs alone in a real multi-tenant service; derive tenant identity from authenticated server-side context and consider PostgreSQL Row-Level Security.

## 7. Tests and lint

```bash
uv run pytest
uv run ruff check .
```

Unit tests do not require Docker. The database commands do.

## Folder structure

```text
task05_vector_database_engineering/
├── .env.example
├── .gitignore
├── .python-version
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── sql/
│   └── 001_init.sql
├── src/task05_vector_db/
│   ├── __init__.py
│   ├── benchmark.py
│   ├── chroma_store.py
│   ├── cli.py
│   ├── config.py
│   ├── embeddings.py
│   └── repository.py
└── tests/
    ├── test_benchmark.py
    ├── test_embeddings.py
    └── test_repository_validation.py
```

## Interview notes

1. **HNSW vs IVFFlat:** HNSW traverses a multi-layer proximity graph. IVFFlat partitions vectors into centroid-based lists and probes selected lists. HNSW commonly trades more RAM/build time for higher recall; IVFFlat can build faster but needs representative data and probe tuning.
2. **Why pgvector:** relational joins, ACID transactions, one backup/security model, and reduced synchronization between separate relational and vector systems.
3. **HNSW memory:** vector payload for 1M × 1536 float32 values is about 6.14 GB decimal (about 5.72 GiB), before tuple/index/graph overhead. Actual index/RAM needs depend on pgvector version, row overhead, graph settings, and workload; measure rather than assume a fixed multiplier.
4. **Filtering:** applying a tenant predicate in the same SQL query prevents cross-tenant rows from being returned. ANN indexes and highly selective filters can affect recall/result counts; evaluate filtered recall and consider iterative scans, partitioning, or exact search for small tenant subsets.
5. **MVCC and maintenance:** updates create new row versions; vacuum reclaims dead tuples, and index maintenance/reindexing may be needed when bloat is observed. Monitor autovacuum and query plans.

## Production hardening checklist

- Use real embeddings of a fixed model and enforce matching dimensions/model versions.
- Derive tenant identity from authenticated authorization context; evaluate RLS.
- Add migrations rather than relying on init scripts for existing deployments.
- Benchmark filtered recall, p95/p99 latency, QPS, index build time, and memory on representative data.
- Tune `maintenance_work_mem`, `work_mem`, `shared_buffers`, index parameters, and connection pooling based on measurements.
- Add retries/timeouts, observability, backups, secrets management, and integration tests against the deployed PostgreSQL version.
