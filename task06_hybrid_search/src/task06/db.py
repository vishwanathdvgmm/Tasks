from contextlib import contextmanager
import psycopg
from pgvector.psycopg import register_vector
from .config import DATABASE_URL

@contextmanager
def connect():
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        yield conn

def initialize_schema() -> None:
    # Create extension on a raw connection before register_vector is called
    with psycopg.connect(DATABASE_URL) as raw_conn:
        raw_conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    sql = """
    CREATE TABLE IF NOT EXISTS documents (
        id BIGSERIAL PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        external_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR(384) NOT NULL,
        search_vector TSVECTOR GENERATED ALWAYS AS
          (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))) STORED,
        UNIQUE (tenant_id, external_id)
    );
    CREATE INDEX IF NOT EXISTS documents_tenant_idx ON documents (tenant_id);
    CREATE INDEX IF NOT EXISTS documents_search_vector_idx
      ON documents USING GIN (search_vector);
    CREATE INDEX IF NOT EXISTS documents_embedding_idx
      ON documents USING hnsw (embedding vector_cosine_ops);
    """
    with connect() as conn:
        conn.execute(sql)
