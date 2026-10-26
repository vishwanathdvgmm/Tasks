from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from .config import DATABASE_URL

pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=False)

def init_db():
    pool.open(wait=True)
    with pool.connection() as conn:
        register_vector(conn)
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()

@contextmanager
def connection():
    with pool.connection() as conn:
        register_vector(conn)
        yield conn
