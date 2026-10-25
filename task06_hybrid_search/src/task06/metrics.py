def reciprocal_rank_at_k(results: list[str], relevant: set[str], k: int = 5) -> float:
    for rank, doc_id in enumerate(results[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0

def recall_at_k(results: list[str], relevant: set[str], k: int = 5) -> float:
    if not relevant:
        return 0.0
    return len(set(results[:k]) & relevant) / len(relevant)

def precision_at_k(results: list[str], relevant: set[str], k: int = 5) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return len(set(results[:k]) & relevant) / k

def evaluate(
    runs: dict[str, list[list[str]]],
    qrels: list[set[str]],
    k: int = 5,
) -> dict[str, dict[str, float]]:
    """Evaluate multiple systems across queries; qrels contains relevant IDs per query."""
    report = {}
    for system, query_results in runs.items():
        if len(query_results) != len(qrels):
            raise ValueError(f"{system}: result query count does not match qrels")
        report[system] = {
            "precision@k": sum(precision_at_k(r, rel, k) for r, rel in zip(query_results, qrels)) / max(1, len(qrels)),
            "recall@k": sum(recall_at_k(r, rel, k) for r, rel in zip(query_results, qrels)) / max(1, len(qrels)),
            "mrr@k": sum(reciprocal_rank_at_k(r, rel, k) for r, rel in zip(query_results, qrels)) / max(1, len(qrels)),
        }
    return report
