from task11_guardrails.metrics import (
    lexical_answer_relevance,
    lexical_context_precision,
    lexical_context_recall,
)


def test_context_metrics():
    truth = "RAG retrieves relevant documents for generation"
    contexts = ["RAG retrieves documents", "A recipe for pancakes"]
    assert lexical_context_precision(contexts, truth) == 0.5
    assert lexical_context_recall(contexts, truth) > 0.5

def test_answer_relevance_proxy():
    assert lexical_answer_relevance("RAG retrieves documents", "What does RAG retrieve?") > 0
