from .db import connect
from .embeddings import embed_texts
from .models import SearchResult
from .rrf import reciprocal_rank_fusion
from .reranker import rerank

def _result(row, score: float, source: str) -> SearchResult:
    return SearchResult(row[0], row[1], row[2], float(score), source)

def vector_search(query: str, tenant_id: str, limit: int = 50) -> list[SearchResult]:
    vector = embed_texts([query])[0]
    with connect() as conn:
        rows = conn.execute(
            """SELECT external_id, title, content, 1 - (embedding <=> %s::vector) AS score
               FROM documents WHERE tenant_id = %s
               ORDER BY embedding <=> %s::vector LIMIT %s""",
            (vector, tenant_id, vector, limit),
        ).fetchall()
    return [_result(row, row[3], "vector") for row in rows]

def lexical_search(query: str, tenant_id: str, limit: int = 50) -> list[SearchResult]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT external_id, title, content,
                      ts_rank_cd(search_vector, websearch_to_tsquery('english', %s)) AS score
               FROM documents
               WHERE tenant_id = %s
                 AND search_vector @@ websearch_to_tsquery('english', %s)
               ORDER BY score DESC, external_id
               LIMIT %s""",
            (query, tenant_id, query, limit),
        ).fetchall()
    return [_result(row, row[3], "lexical") for row in rows]

def hybrid_search(
    query: str, tenant_id: str, candidate_k: int = 50, top_k: int = 5,
    use_reranker: bool = True
) -> list[SearchResult]:
    dense = vector_search(query, tenant_id, candidate_k)
    sparse = lexical_search(query, tenant_id, candidate_k)
    fused = reciprocal_rank_fusion([dense, sparse], k=60)[:candidate_k]
    return rerank(query, fused, top_k) if use_reranker else fused[:top_k]
