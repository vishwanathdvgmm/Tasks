from __future__ import annotations
import re
from .models import Citation, RetrievedChunk

GROUNDED_SYSTEM_PROMPT = """You are an enterprise RAG assistant. Answer ONLY with facts explicitly supported by the supplied context. Do not use outside knowledge or infer missing details. If the context is insufficient, say: 'I don't know based on the available documents.' Every factual claim must include a citation in the form [chunk_id, p. N]. Never invent sources, page numbers, or quotations."""

class MockLLMProvider:
    """No API key required. Extracts relevant source sentences for deterministic demos."""
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> tuple[str, list[Citation]]:
        if not chunks:
            return "I don't know based on the available documents.", []
        q_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
        candidates: list[tuple[float, RetrievedChunk, str]] = []
        for chunk in chunks:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.text):
                terms = set(re.findall(r"[a-z0-9]+", sentence.lower()))
                overlap = len(q_terms & terms) / max(len(q_terms), 1)
                score = overlap + chunk.score * 0.25
                if overlap > 0:
                    candidates.append((score, chunk, sentence.strip()))
        candidates.sort(key=lambda x: x[0], reverse=True)
        selected: list[tuple[RetrievedChunk, str]] = []
        seen = set()
        for _, chunk, sentence in candidates:
            key = (chunk.chunk_id, sentence)
            if key not in seen:
                selected.append((chunk, sentence))
                seen.add(key)
            if len(selected) >= 3:
                break
        if not selected:
            return "I don't know based on the available documents.", []
        citations = [Citation(chunk_id=c.chunk_id, source_filename=c.source_filename, page_number=c.page_number, quote=s) for c, s in selected]
        answer = " ".join(f"{sentence} [{chunk.chunk_id}, p. {chunk.page_number}]" for chunk, sentence in selected)
        return answer, citations
