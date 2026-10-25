from collections import defaultdict
from .models import SearchResult

def reciprocal_rank_fusion(
    ranked_lists: list[list[SearchResult]], k: int = 60
) -> list[SearchResult]:
    """Fuse ranked lists using 1/(k + 1-based rank), aggregating by external_id."""
    if k < 1:
        raise ValueError("k must be >= 1")
    scores: dict[str, float] = defaultdict(float)
    representatives: dict[str, SearchResult] = {}
    for results in ranked_lists:
        seen: set[str] = set()
        for rank, result in enumerate(results, start=1):
            if result.external_id in seen:
                continue
            seen.add(result.external_id)
            scores[result.external_id] += 1.0 / (k + rank)
            representatives.setdefault(result.external_id, result)
    return [
        SearchResult(
            external_id=representatives[key].external_id,
            title=representatives[key].title,
            content=representatives[key].content,
            score=score,
            source="hybrid+rrf",
        )
        for key, score in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
