from functools import lru_cache
from .config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Create normalized local embeddings; the first run downloads the model."""
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()
