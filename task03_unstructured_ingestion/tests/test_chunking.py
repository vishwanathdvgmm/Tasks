from task03_ingestion.chunking import (
    markdown_header_chunks, recursive_chunks, semantic_chunks, sliding_window_chunks,
)
from task03_ingestion.tokenization import TokenCounter

def test_all_strategies_respect_token_budget():
    counter = TokenCounter()
    text = ("# Heading\n\nA sentence about retrieval and chunking. " * 100)
    outputs = [
        recursive_chunks(text, counter, 40, 5),
        sliding_window_chunks(text, counter, 40, 5),
        [c for _, c in markdown_header_chunks(text, counter, 40, 5)],
        semantic_chunks(text, counter, 40, 5),
    ]
    for chunks in outputs:
        assert chunks
        assert all(counter.count(c) <= 40 for c in chunks)

def test_sliding_window_rejects_invalid_overlap():
    counter = TokenCounter()
    try:
        sliding_window_chunks("hello", counter, 10, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
