import numpy as np
import pytest
from vector_embeddings.metrics import (
    cosine_similarity, dot_product, euclidean_distance, l2_normalize,
)

def test_cosine_similarity_ignores_magnitude():
    assert cosine_similarity([1, 2], [10, 20]) == pytest.approx(1.0)

def test_dot_product_depends_on_magnitude():
    assert dot_product([1, 2], [10, 20]) == pytest.approx(50.0)

def test_normalized_dot_equals_cosine():
    a, b = [1, 2, 3], [3, 1, 0]
    assert dot_product(l2_normalize(a), l2_normalize(b)) == pytest.approx(cosine_similarity(a, b))

def test_euclidean_distance():
    assert euclidean_distance([0, 0], [3, 4]) == pytest.approx(5.0)

def test_normalization_has_unit_norm():
    assert np.linalg.norm(l2_normalize([3, 4])) == pytest.approx(1.0)

@pytest.mark.parametrize("a,b", [([1], [1, 2]), ([[1, 2]], [[1, 2]]), ([0, 0], [1, 1])])
def test_invalid_cosine_inputs(a, b):
    with pytest.raises(ValueError):
        cosine_similarity(a, b)

def test_zero_vector_cannot_be_normalized():
    with pytest.raises(ValueError):
        l2_normalize([0, 0])
