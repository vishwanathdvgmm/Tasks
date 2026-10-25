import pytest
from task05_vector_db.repository import PgVectorRepository

def test_upsert_rejects_wrong_dimensions_before_connecting():
    repo = PgVectorRepository("postgresql://invalid", dimensions=3)
    with pytest.raises(ValueError, match="expected 3 dimensions"):
        repo.upsert("tenant", "id", "content", [0.1, 0.2])

def test_search_rejects_empty_tenant_before_connecting():
    repo = PgVectorRepository("postgresql://invalid", dimensions=3)
    with pytest.raises(ValueError, match="tenant_id"):
        repo.search(" ", [0.1, 0.2, 0.3])

def test_search_rejects_wrong_dimensions_before_connecting():
    repo = PgVectorRepository("postgresql://invalid", dimensions=3)
    with pytest.raises(ValueError, match="expected 3 dimensions"):
        repo.search("tenant", [0.1], limit=2)
