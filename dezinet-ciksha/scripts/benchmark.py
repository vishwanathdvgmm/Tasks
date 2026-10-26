"""Small retrieval ranking benchmark. Replace fixture labels with a curated gold dataset."""
from collections import defaultdict

# Minimal deterministic fixture for validating metric calculation, not a quality claim.
FIXTURE = [
    {"query": "tenant isolation", "relevant": {"chunk-2"}, "ranked": ["chunk-1", "chunk-2", "chunk-3"]},
    {"query": "streaming citations", "relevant": {"chunk-4", "chunk-5"}, "ranked": ["chunk-4", "chunk-9", "chunk-5"]},
    {"query": "vector indexing", "relevant": {"chunk-7"}, "ranked": ["chunk-8", "chunk-7", "chunk-1"]},
]

def reciprocal_rank(ranked, relevant, k=5):
    for rank, item in enumerate(ranked[:k], start=1):
        if item in relevant:
            return 1 / rank
    return 0.0

def hit_rate(ranked, relevant, k=5):
    return float(any(item in relevant for item in ranked[:k]))

if __name__ == "__main__":
    mrr = sum(reciprocal_rank(x["ranked"], x["relevant"]) for x in FIXTURE) / len(FIXTURE)
    hit = sum(hit_rate(x["ranked"], x["relevant"]) for x in FIXTURE) / len(FIXTURE)
    print(f"Fixture MRR@5: {mrr:.3f}")
    print(f"Fixture Hit Rate@5: {hit:.3f}")
    print("NOTE: These are fixture metrics only, not a benchmark of the live application.")
