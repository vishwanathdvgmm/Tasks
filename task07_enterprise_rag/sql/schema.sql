-- Optional PostgreSQL + pgvector schema for the production persistence layer.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_filename TEXT NOT NULL,
    page_number INTEGER NOT NULL CHECK (page_number >= 1),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_chunks_tenant_idx ON document_chunks (tenant_id);
CREATE INDEX IF NOT EXISTS document_chunks_search_idx ON document_chunks USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Example hybrid retrieval query (bind tenant_id, query_text, and query_embedding).
-- Dense similarity: 1 - cosine distance. Lexical rank: ts_rank_cd.
-- In production, normalize both scores and fuse using RRF or a calibrated reranker.
-- SELECT chunk_id, source_filename, page_number, content,
--        1 - (embedding <=> %(query_embedding)s::vector) AS dense_score,
--        ts_rank_cd(search_vector, websearch_to_tsquery('english', %(query_text)s)) AS lexical_score
-- FROM document_chunks
-- WHERE tenant_id = %(tenant_id)s
--   AND (search_vector @@ websearch_to_tsquery('english', %(query_text)s) OR embedding IS NOT NULL)
-- ORDER BY (0.6 * (1 - (embedding <=> %(query_embedding)s::vector)) +
--           0.4 * ts_rank_cd(search_vector, websearch_to_tsquery('english', %(query_text)s))) DESC
-- LIMIT 10;
