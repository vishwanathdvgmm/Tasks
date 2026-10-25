import numpy as np
import pytest
from task05_vector_db.embeddings import demo_embedding

def test_embedding_is_stable_and_dimensioned():
    first = demo_embedding("same text", 64)
    second = demo_embedding("same text", 64)
    assert first == second
    assert len(first) == 64
    assert np.linalg.norm(first) == pytest.approx(1.0, abs=1e-5)

def test_different_texts_produce_different_vectors():
    assert demo_embedding("alpha", 64) != demo_embedding("beta", 64)

def test_invalid_dimension_rejected():
    with pytest.raises(ValueError):
        demo_embedding("text", 0)
