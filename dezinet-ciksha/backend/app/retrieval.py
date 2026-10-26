from collections import defaultdict
from .db import connection
from .llm import embed

async def hybrid_search(tenant_id: str, query: str, top_k: int = 5) -> list[dict]:
    vector = await embed(query)
    with connection() as conn:
        dense_rows = conn.execute(
            """SELECT id, document_id, content, chunk_index,
                      1 - (embedding <=> %s::vector) AS score
               FROM chunks WHERE tenant_id = %s AND embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector LIMIT %s""",
            (vector, tenant_id, vector, top_k * 4)
        ).fetchall()
        # PostgreSQL full-text lexical search; reciprocal rank fusion combines both lists.
        lexical_rows = conn.execute(
            """SELECT id, document_id, content, chunk_index,
                      ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) AS score
               FROM chunks
               WHERE tenant_id = %s
                 AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
               ORDER BY score DESC LIMIT %s""",
            (query, tenant_id, query, top_k * 4)
        ).fetchall()

    fused = defaultdict(lambda: {"rrf": 0.0})
    for rank, row in enumerate(dense_rows, 1):
        cid, doc_id, content, idx, score = row
        fused[cid].update({"id": cid, "document_id": str(doc_id), "content": content,
                           "chunk_index": idx, "dense_score": float(score or 0)})
        fused[cid]["rrf"] += 1 / (60 + rank)
    for rank, row in enumerate(lexical_rows, 1):
        cid, doc_id, content, idx, score = row
        fused[cid].update({"id": cid, "document_id": str(doc_id), "content": content,
                           "chunk_index": idx, "lexical_score": float(score or 0)})
        fused[cid]["rrf"] += 1 / (60 + rank)
    return sorted(fused.values(), key=lambda item: item["rrf"], reverse=True)[:top_k]
