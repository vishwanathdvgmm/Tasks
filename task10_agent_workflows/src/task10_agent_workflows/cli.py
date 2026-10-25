from __future__ import annotations

import argparse
import json
from .checkpoint import CheckpointStore
from .graph import StateGraph

def main() -> None:
    parser = argparse.ArgumentParser(prog="task10", description="Task 10 stateful agent workflow demo")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run a new workflow")
    run_parser.add_argument("request", help="user task")
    run_parser.add_argument("--require-approval", action="store_true")
    run_parser.add_argument("--max-steps", type=int, default=12)
    run_parser.add_argument("--max-revisions", type=int, default=2)
    run_parser.add_argument("--checkpoint-dir", default=".task10_checkpoints")

    resume_parser = sub.add_parser("resume", help="resume a paused workflow")
    resume_parser.add_argument("approval_id")
    resume_parser.add_argument("--decision", choices=["approve", "reject"], required=True)
    resume_parser.add_argument("--checkpoint-dir", default=".task10_checkpoints")

    sub.add_parser("graph", help="print graph transitions")

    args = parser.parse_args()
    if args.command == "graph":
        print(StateGraph.graph_description())
        return

    store = CheckpointStore(getattr(args, "checkpoint_dir", ".task10_checkpoints"))
    graph = StateGraph(checkpoint_store=store)
    if args.command == "run":
        state = graph.run(
            args.request,
            require_approval=args.require_approval,
            max_steps=args.max_steps,
            max_revisions=args.max_revisions,
        )
    else:
        state = graph.resume(args.approval_id, args.decision)

    print(json.dumps(state.model_dump(mode="json"), indent=2))
    if state.status == "paused":
        print(f"\nAPPROVAL REQUIRED: run `uv run task10 resume {state.approval_id} --decision approve`")
    elif state.status == "completed":
        print("\nFINAL OUTPUT\n" + state.final_output)

if __name__ == "__main__":
    main()
