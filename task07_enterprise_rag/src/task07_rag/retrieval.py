from __future__ import annotations
import math
import re
from collections import Counter
from .models import DocumentChunk, RetrievedChunk

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

def cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(value * b.get(term, 0) for term, value in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

class MemoryHybridRetriever:
    """Local BM25-like lexical + token-vector cosine retrieval.

    The token-vector component is a deterministic stand-in for dense embeddings;
    production deployments should replace it with a real embedding model.
    """
    def __init__(self, chunks: list[DocumentChunk]):
        self.chunks = chunks
        self.tokens = {c.chunk_id: tokenize(c.text) for c in chunks}
        self.doc_freq = Counter(term for terms in self.tokens.values() for term in set(terms))

    def search(self, queries: list[str], top_k: int = 5) -> list[RetrievedChunk]:
        scores: dict[str, float] = {}
        methods: dict[str, str] = {}
        for query in queries:
            q_tokens = tokenize(query)
            q_counts = Counter(q_tokens)
            for chunk in self.chunks:
                d_tokens = self.tokens[chunk.chunk_id]
                d_counts = Counter(d_tokens)
                # Lightweight BM25-inspired lexical score with length normalization.
                lexical = 0.0
                for term, qtf in q_counts.items():
                    tf = d_counts.get(term, 0)
                    if tf:
                        idf = math.log(1 + (len(self.chunks) - self.doc_freq[term] + 0.5) / (self.doc_freq[term] + 0.5))
                        lexical += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * len(d_tokens) / 40)) * min(qtf, 2)
                dense = cosine(Counter(q_tokens), d_counts)
                combined = 0.65 * min(lexical / 3.0, 1.0) + 0.35 * dense
                if combined > scores.get(chunk.chunk_id, 0.0):
                    scores[chunk.chunk_id] = combined
                    methods[chunk.chunk_id] = "lexical+dense"
        by_id = {c.chunk_id: c for c in self.chunks}
        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]
        return [RetrievedChunk(**by_id[cid].model_dump(), score=score, retrieval_method=methods[cid]) for cid, score in ranked]
