from vector_embeddings.providers import MockEmbeddingProvider

def test_mock_provider_is_deterministic_and_fixed_dimension():
    provider = MockEmbeddingProvider(12)
    first = provider.embed(["same text"])[0]
    second = provider.embed(["same text"])[0]
    assert first == second
    assert len(first) == 12
