from .metrics import evaluate
from .retrieval import vector_search, lexical_search, hybrid_search

BENCHMARK_QUERIES = [
    ("What causes ERR-5034?", {"err-5034", "incident-5034"}),
    ("Find product SKU XJ-204", {"sku-xj-204"}),
    ("What does clause 9.2 say about retention?", {"clause-9-2"}),
    ("How do we combine ranked retrieval results?", {"rrf"}),
    ("How can candidate relevance be improved after retrieval?", {"cross-encoder"}),
]

def run_benchmark(tenant_id: str = "org_demo", k: int = 5) -> dict:
    runs = {"vector-only": [], "lexical-only": [], "hybrid+rerank": []}
    qrels = []
    for query, relevant in BENCHMARK_QUERIES:
        qrels.append(relevant)
        runs["vector-only"].append([r.external_id for r in vector_search(query, tenant_id, 50)[:k]])
        runs["lexical-only"].append([r.external_id for r in lexical_search(query, tenant_id, 50)[:k]])
        runs["hybrid+rerank"].append([r.external_id for r in hybrid_search(query, tenant_id, 50, k, True)])
    return evaluate(runs, qrels, k)
