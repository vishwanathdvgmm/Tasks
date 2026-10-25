# Task 10 — Autonomous Multi-Step AI Agents & Workflow Graphs

A runnable, API-key-free demonstration of stateful agent orchestration using a custom typed state graph. It uses a deterministic mock model so tests are repeatable. The graph demonstrates planning, retrieval, controlled tool execution, conditional routing, reviewer feedback, bounded retries, JSON checkpoint persistence, and human-in-the-loop approval.

> Safety note: the "code executor" is a controlled tool dispatcher, not arbitrary Python `exec`. The destructive action is simulated and cannot send real email, transfer money, or mutate external systems.

## Requirements

- Python 3.11+
- `uv`

## Setup

```bash
uv sync
uv run pytest
uv run task10 run "Research agent workflows and calculate 12 * 7"
```

## Try the human approval flow

```bash
uv run task10 run "Prepare a simulated destructive action" --require-approval
```

The command pauses and prints an approval ID and checkpoint path. Resume using that ID:

```bash
uv run task10 resume APPROVAL_ID --decision approve
# or
uv run task10 resume APPROVAL_ID --decision reject
```

Checkpoints are stored under `.task10_checkpoints/` in the current working directory by default. You can override this with `--checkpoint-dir`.

## Architecture

- `AgentState` is a Pydantic state schema.
- `StateGraph` maps node names to node functions and uses conditional routing.
- `planner` creates a bounded plan.
- `researcher` retrieves from a local mock knowledge base.
- `executor` dispatches only allow-listed tools.
- `reviewer` evaluates the result and provides revision feedback.
- Failed verification routes back to execution, with a maximum iteration count.
- `approval_gate` checkpoints and pauses before a simulated destructive action.
- `output` formats the final result.
- `fallback` safely terminates when limits are reached.

## Example graph

```text
START -> planner -> researcher -> executor -> reviewer
                                      ^          |
                                      |-- revise-|
                                                 |
                                      pass -> approval_gate -> output -> END
```

## Design notes

- **ReAct:** this sample uses a deterministic Plan/Act/Observe/Review loop. A live model can replace `MockModel` without changing graph routing.
- **State vs memory:** `AgentState` is short-term run state; JSON checkpoints persist an in-progress run. Long-term user memory is intentionally out of scope.
- **Recursion / loops:** the runner enforces `max_steps` and `max_revisions`; it never loops indefinitely.
- **HITL:** approval is represented as a persisted `paused` state. Resume loads the saved state and validates the approval decision.
- **Production extensions:** replace JSON checkpoints with PostgreSQL/Redis, add authentication and authorization around approval IDs, and use an audited external tool layer with idempotency keys.

## CLI

```bash
uv run task10 run "your request"
uv run task10 run "your request" --require-approval
uv run task10 resume APPROVAL_ID --decision approve
uv run task10 resume APPROVAL_ID --decision reject
uv run task10 graph
```
