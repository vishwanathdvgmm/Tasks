"""Dependency-free baseline metrics for fast CI smoke tests.

These are lexical proxies, NOT substitutes for RAGAS or a human evaluation.
Use RAGAS/LLM judges for semantic faithfulness and relevance.
"""
import re

_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "should",
    "shouldn't", "so", "some", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "were", "weren't", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "won't", "would", "wouldn't", "you", "your", "yours",
    "yourself", "yourselves",
}

def _tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"\b[a-z0-9]+\b", text.lower()))
    content_tokens = tokens - _STOPWORDS
    return content_tokens or tokens

def lexical_context_precision(contexts: list[str], ground_truth: str) -> float:
    """Fraction of non-empty contexts sharing at least one token with ground truth."""
    if not contexts:
        return 0.0
    truth = _tokens(ground_truth)
    if not truth:
        return 0.0
    hits = sum(bool(_tokens(ctx) & truth) for ctx in contexts)
    return hits / len(contexts)

def lexical_context_recall(contexts: list[str], ground_truth: str) -> float:
    """Fraction of ground-truth tokens appearing in the retrieved context union."""
    truth = _tokens(ground_truth)
    if not truth:
        return 0.0
    found = set().union(*(_tokens(ctx) for ctx in contexts)) if contexts else set()
    return len(truth & found) / len(truth)

def lexical_answer_relevance(answer: str, question: str) -> float:
    q = _tokens(question)
    a = _tokens(answer)
    return len(q & a) / len(q) if q else 0.0
