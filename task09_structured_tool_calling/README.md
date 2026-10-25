# Task 09 — Structured Output Generation & Function / Tool Calling

A runnable learning project for Pydantic v2 validation, JSON Schema, tool registries,
parallel async execution, defensive parsing, and a bounded retry loop.

## Requirements

- Python 3.11+
- `uv`

## Install and test

```bash
uv sync --extra dev
uv run pytest
```

Run the mock demonstration (no API key required):

```bash
uv run task09 demo
uv run task09 structured
uv run task09 tools
```

## Optional OpenAI provider

Install the optional SDK and set your API key in the shell:

```bash
uv sync --extra dev --extra openai
# Windows PowerShell:
$env:OPENAI_API_KEY="your-key"
# Git Bash:
export OPENAI_API_KEY="your-key"
uv run task09 openai "Calculate 19 * 23 and explain the result"
```

The OpenAI provider uses Chat Completions tool calls and strict JSON Schema response
format. Model availability and supported schema features depend on the model selected
with `OPENAI_MODEL` (default: `gpt-4o-mini`).

## Architecture

- `schemas.py`: strict Pydantic models and JSON Schema.
- `tools.py`: calculator, deterministic demo weather, safe read-only SQL example, and
  mock web search.
- `registry.py`: allow-listed tool registry; validates arguments before execution.
- `providers.py`: deterministic mock provider and optional OpenAI adapter.
- `agent.py`: bounded tool-calling loop; independent calls run concurrently with
  `asyncio.gather`.
- `retry.py`: defensive JSON parsing and bounded schema repair/retry utility.
- `cli.py`: demo entry points.

## Safety notes

- Tool names must exist in the allow-list.
- Tool arguments are validated before execution.
- Tool exceptions are returned as structured tool errors instead of crashing the loop.
- SQL is restricted to a small, fixed, read-only demo query. Do not execute arbitrary
  model-generated SQL against a production database.
- A real deployment should use read-only credentials, parameterized queries, tenant
  isolation, timeouts, rate limits, audit logging, and human approval for mutations.
- Structured Outputs constrain format, but do not guarantee factual correctness or
  make tool execution inherently safe. Validate business rules separately.
