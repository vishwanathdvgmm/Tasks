from functools import lru_cache
from .config import RERANKER_MODEL
from .models import SearchResult

@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(RERANKER_MODEL)

def rerank(query: str, candidates: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
    """Score query/document pairs jointly using a local cross-encoder."""
    if not candidates:
        return []
    pairs = [(query, f"{item.title}\n{item.content}") for item in candidates]
    scores = _model().predict(pairs)
    ranked = [
        SearchResult(item.external_id, item.title, item.content, float(score), "hybrid+rerank")
        for item, score in zip(candidates, scores)
    ]
    return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]
