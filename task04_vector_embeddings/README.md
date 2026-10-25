# Task 04 — Vector Embeddings, Dimensionality & Similarity Metrics

A runnable learning project for embedding generation, vector math, batch retries, and embedding caching. Uses `uv`.

## Quick start (Windows PowerShell)

```powershell
uv sync --extra dev
uv run pytest
uv run embeddings-demo
```

The mock provider is deterministic and does not require an API key, Redis, or internet access. Its vectors are **pseudo-embeddings for testing plumbing only**; do not use them to judge semantic relevance.

## Project structure

```text
task04_vector_embeddings/
├── pyproject.toml
├── uv.lock                 # created by `uv lock` / `uv sync`
├── .env.example
├── README.md
├── src/vector_embeddings/
│   ├── cache.py            # normalized SHA-256 keys and cache adapters
│   ├── cli.py              # runnable demo
│   ├── metrics.py          # cosine, dot product, L2, normalization
│   ├── providers.py        # mock, OpenAI, local Sentence-Transformers
│   └── service.py          # batching, retries, caching, deduplication
└── tests/
    ├── test_cache_and_service.py
    ├── test_metrics.py
    └── test_provider_contract.py
```

## Optional providers

### OpenAI

Set an API key in the current PowerShell session, then run:

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
uv run embeddings-demo --provider openai "search engines" "information retrieval"
```

Use `text-embedding-3-large` if its accuracy/cost profile fits your workload. OpenAI's third-generation embedding models support a `dimensions` request parameter; this starter adapter leaves that parameter at the provider default. Add it explicitly if testing reduced dimensions.

### Local Sentence-Transformers / BGE

```powershell
uv sync --extra dev --extra local
uv run embeddings-demo --provider local --model BAAI/bge-small-en-v1.5 "semantic search" "document retrieval"
```

The first run may download model weights and PyTorch dependencies. Local models do not require an OpenAI API key.

### Redis cache

Start Redis locally (for example, with Docker):

```powershell
docker run --rm --name task04-redis -p 6379:6379 redis:7-alpine
```

`RedisCache` is available in `vector_embeddings.cache`:

```python
from vector_embeddings.cache import RedisCache
from vector_embeddings.providers import OpenAIEmbeddingProvider
from vector_embeddings.service import EmbeddingService

service = EmbeddingService(
    provider=OpenAIEmbeddingProvider(),
    cache=RedisCache("redis://localhost:6379/0"),
)
vectors = service.embed_texts(["What is vector search?"])
```

The default cache TTL is 30 days. Cache keys include a version, a hash of the model name, and a SHA-256 digest of normalized text. Include any additional model configuration (dimensions, preprocessing version, task/prompt mode) in the cache namespace in production. Normalization is a product decision: lowercasing is appropriate for many search use cases but not all text or embedding models.

## Mathematics

For vectors \(a,b\):

- **Dot product:** \(a \cdot b = \sum_i a_i b_i\). Magnitudes affect the result.
- **Cosine similarity:** \(\frac{a \cdot b}{\|a\|\_2\|b\|\_2}\). Measures angle; zero vectors are undefined.
- **Euclidean distance:** \(\|a-b\|\_2\). Smaller values indicate closer points.
- **L2 normalization:** \(\hat a = a / \|a\|\_2\). For unit vectors, dot product equals cosine similarity (within floating-point tolerance).

Metric choice depends on how the model was trained and how the index is configured. Cosine and dot product rankings are identical for normalized vectors. Euclidean distance rankings are also equivalent to cosine rankings for unit vectors because \(\|\hat a-\hat b\|\_2^2=2-2\cos(\hat a,\hat b)\).

## Reliability and cache behavior

- The service deduplicates normalized text within a request.
- Missing entries are sent to the provider in batches capped by `batch_size`.
- Retry delays are exponential: `base_delay * 2**attempt` (no jitter in this educational version).
- Cache identity includes the model name so two models do not accidentally share vectors.
- Redis failures currently propagate; production systems should decide whether to fail open (bypass cache) or fail closed based on cost and availability requirements.
- The current retry wrapper retries all exceptions. In production, retry transient timeouts, rate limits, and server errors; avoid retrying permanent authentication or invalid-request errors.

## Interview notes

1. **Cosine vs dot product:** dot product is magnitude-sensitive; cosine divides by both norms. They are equal when both vectors have unit L2 norm.
2. **Curse of dimensionality:** in high dimensions, distances may concentrate and become less discriminative; storage and compute also rise. ANN indexes and quantization can help at scale, but they are not automatically required for every workload.
3. **Matryoshka representations:** models trained with Matryoshka Representation Learning can preserve useful information in leading dimensions, allowing truncation with a quality/storage trade-off. Support and accuracy loss are model- and task-dependent; never assume a fixed 1–2% loss without measuring.
4. **Embedding cache:** use a stable hash of normalized text and model/config identity. Hashing avoids storing raw text in keys, but does not make cached vectors or cache access inherently private.
5. **MTEB:** benchmark suite covering multiple embedding tasks. Select models using task-specific evaluation (e.g. Recall@k, MRR@k, NDCG@k), latency, memory, dimensions, license, and cost—not a single leaderboard score.

## Suggested assignment demo

1. Run tests.
2. Run `uv run embeddings-demo`.
3. Explain why the mock provider is not a semantic benchmark.
4. Compare raw dot product and cosine for vectors with different magnitudes.
5. Show that normalized dot product equals cosine.
6. Explain cache hit/miss behavior and why model identity belongs in the key.
7. If environment allows, run Redis and one real provider; keep secrets out of source control.
