CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    external_id TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(1536) NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, external_id)
);

CREATE INDEX IF NOT EXISTS documents_tenant_idx ON documents (tenant_id);
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING GIN (metadata);

-- Choose ONE ANN index for experiments. The CLI can create either index explicitly.
-- HNSW: CREATE INDEX documents_embedding_hnsw ON documents
--       USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- IVFFlat: CREATE INDEX documents_embedding_ivfflat ON documents
--          USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
