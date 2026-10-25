from __future__ import annotations

import json
from typing import Any, Literal

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

IndexKind = Literal["hnsw", "ivfflat"]

class PgVectorRepository:
    """Small repository emphasizing tenant-scoped SQL and explicit index controls."""

    def __init__(self, dsn: str, dimensions: int = 1536):
        self.dsn = dsn
        self.dimensions = dimensions

    def connect(self):
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        register_vector(conn)
        return conn

    def ping(self) -> bool:
        with self.connect() as conn:
            conn.execute("SELECT 1")
        return True

    def upsert(
        self, tenant_id: str, external_id: str, content: str,
        embedding: list[float] | np.ndarray, metadata: dict[str, Any] | None = None,
    ) -> int:
        if not tenant_id.strip():
            raise ValueError("tenant_id must not be empty")
        if len(embedding) != self.dimensions:
            raise ValueError(f"expected {self.dimensions} dimensions, got {len(embedding)}")
        vec = np.asarray(embedding, dtype=np.float32)
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO documents (tenant_id, external_id, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (tenant_id, external_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING id
                """,
                (tenant_id, external_id, content, vec,
                 json.dumps(metadata or {})),
            ).fetchone()
            return int(row["id"])

    def search(
        self, tenant_id: str, query_embedding: list[float] | np.ndarray, limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
        metric: Literal["cosine", "l2", "inner_product"] = "cosine",
    ) -> list[dict[str, Any]]:
        """Search only within tenant_id; metric operators match pgvector conventions."""
        if not tenant_id.strip():
            raise ValueError("tenant_id must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")
        if len(query_embedding) != self.dimensions:
            raise ValueError(f"expected {self.dimensions} dimensions, got {len(query_embedding)}")
        operator = {"cosine": "<=>", "l2": "<->", "inner_product": "<#>"}[metric]
        # Operator is selected from a fixed allowlist above; user input is never interpolated.
        distance_alias = {"cosine": "distance", "l2": "distance", "inner_product": "negative_inner_product"}[metric]
        where_metadata = "AND metadata @> %s::jsonb" if metadata_filter else ""
        query_vec = np.asarray(query_embedding, dtype=np.float32)
        sql = f"""
            SELECT id, tenant_id, external_id, content, metadata,
                   embedding {operator} %s AS {distance_alias}
            FROM documents
            WHERE tenant_id = %s {where_metadata}
            ORDER BY embedding {operator} %s
            LIMIT %s
        """
        # The vector is bound separately for the SELECT distance and ORDER BY expressions.
        params: list[Any] = [query_vec, tenant_id]
        if metadata_filter:
            params.append(json.dumps(metadata_filter))
        params.extend([query_vec, limit])
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def create_ann_index(self, kind: IndexKind, *, lists: int = 100) -> None:
        with self.connect() as conn:
            if kind == "hnsw":
                conn.execute("DROP INDEX IF EXISTS documents_embedding_ivfflat")
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
                    ON documents USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """)
                conn.execute("SET hnsw.ef_search = 40")
            elif kind == "ivfflat":
                if lists < 1:
                    raise ValueError("lists must be positive")
                conn.execute("DROP INDEX IF EXISTS documents_embedding_hnsw")
                conn.execute("DROP INDEX IF EXISTS documents_embedding_ivfflat")
                conn.execute(f"""
                    CREATE INDEX documents_embedding_ivfflat
                    ON documents USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {int(lists)})
                """)
            else:
                raise ValueError(f"unsupported index kind: {kind}")

    def set_search_effort(self, *, ef_search: int = 40, probes: int = 10) -> None:
        if ef_search < 1 or probes < 1:
            raise ValueError("search effort values must be positive")
        with self.connect() as conn:
            conn.execute("SELECT set_config('hnsw.ef_search', %s, false)", (str(ef_search),))
            conn.execute("SELECT set_config('ivfflat.probes', %s, false)", (str(probes),))
