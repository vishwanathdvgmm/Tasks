# Task 11 — LLM Evaluation, Benchmarking & Safety Guardrails

Python starter for:

- versioned golden RAG evaluation data
- simple deterministic retrieval/answer checks
- prompt-injection and jailbreak screening
- regex-based PII redaction
- CI regression thresholds

## Setup

```bash
uv sync --extra dev
uv run pytest
```

Optional RAGAS / PII dependencies:

```bash
uv sync --extra eval --extra pii
```

Presidio may require a spaCy model, for example:

```bash
uv run python -m spacy download en_core_web_sm
```

## Important design notes

- The injection detector is a lightweight heuristic, not a complete security boundary.
- Treat retrieved documents as untrusted data; delimit them and never allow their contents to alter system policy.
- Regex detection is not sufficient for all PII. Add Presidio/NER and domain-specific recognizers for production.
- Do not log raw prompts or PII. Keep audit logs to categories, decisions, and opaque request IDs.
- Evaluation scores are estimates. Pin model versions and dataset versions; inspect false positives/negatives.
- `golden_dataset.jsonl` contains illustrative synthetic examples. Replace or expand them using your own source documents and human-validated ground truth.
