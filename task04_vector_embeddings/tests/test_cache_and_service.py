import hashlib
import pytest
from vector_embeddings.cache import MemoryCache, cache_key, normalize_text
from vector_embeddings.providers import MockEmbeddingProvider
from vector_embeddings.service import EmbeddingService

def test_normalization():
    assert normalize_text("  HELLO \n   WORLD  ") == "hello world"

def test_key_uses_sha256_and_model_scope():
    key = cache_key(" Hello ", "model-a")
    digest = hashlib.sha256(b"hello").hexdigest()
    assert digest in key
    assert cache_key("hello", "model-a") == key
    assert cache_key("hello", "model-b") != key

def test_duplicate_text_uses_one_embedding_and_cache_hit():
    provider, cache = MockEmbeddingProvider(8), MemoryCache()
    service = EmbeddingService(provider, cache=cache)
    vectors = service.embed_texts([" Hello ", "hello"])
    assert vectors[0] == vectors[1]
    assert provider.calls == 1
    service.embed_texts(["HELLO"])
    assert provider.calls == 1

def test_batching():
    provider = MockEmbeddingProvider(4)
    service = EmbeddingService(provider, batch_size=2)
    vectors = service.embed_texts(["one", "two", "three", "four", "five"])
    assert len(vectors) == 5
    assert provider.calls == 3

def test_retry_then_success():
    class Flaky:
        model_name = "flaky"
        def __init__(self):
            self.calls = 0
        def embed(self, texts):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("temporary failure")
            return [[1.0, 0.0] for _ in texts]
    delays = []
    provider = Flaky()
    service = EmbeddingService(provider, max_retries=3, base_delay_seconds=0.1, sleep=delays.append)
    assert service.embed_texts(["hello"]) == [[1.0, 0.0]]
    assert provider.calls == 3
    assert delays == [0.1, 0.2]

def test_rejects_empty_text():
    with pytest.raises(ValueError):
        EmbeddingService(MockEmbeddingProvider()).embed_texts(["  "])
