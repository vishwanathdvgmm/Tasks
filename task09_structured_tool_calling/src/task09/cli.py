import argparse
import asyncio
import json
import sys

from .agent import ToolCallingAgent, structured_answer
from .providers import MockProvider, OpenAIProvider
from .registry import ToolRegistry
from .schemas import AnswerEnvelope
from .retry import parse_with_retries

async def _run(args: argparse.Namespace) -> int:
    if args.command == "structured":
        provider = MockProvider()
        answer = await structured_answer(provider, "Explain structured outputs in one paragraph.")
        print(answer.model_dump_json(indent=2))
        print("\nJSON Schema:")
        print(json.dumps(AnswerEnvelope.model_json_schema(), indent=2))
        return 0

    if args.command == "tools":
        registry = ToolRegistry()
        samples = [
            ("calculator", {"expression": "19 * 23"}),
            ("weather", {"city": "Bengaluru"}),
            ("web_search", {"query": "Pydantic v2 JSON schema"}),
            ("safe_sql", {"query_name": "demo_users"}),
            ("calculator", {"expression": "__import__('os').system('whoami')"}),
        ]
        for name, payload in samples:
            print(f"{name}: {await registry.execute(name, payload)}")
        return 0

    provider = OpenAIProvider() if args.command == "openai" else MockProvider()
    prompt = getattr(args, "prompt", None) or "Parallel: get weather for Bengaluru and London."
    result = await ToolCallingAgent(provider).run(prompt)
    print(result.model_dump_json(indent=2))
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(description="Task 09 structured output and tool calling")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run the mock parallel tool-calling demo")
    demo.add_argument("prompt", nargs="?", default="Parallel: get weather for Bengaluru and London.")
    sub.add_parser("structured", help="Demonstrate Pydantic JSON Schema structured output")
    sub.add_parser("tools", help="Run tools directly, including an unsafe-expression rejection")
    openai = sub.add_parser("openai", help="Use the optional OpenAI provider")
    openai.add_argument("prompt", nargs="?", default="Calculate 19 * 23 and explain the result")
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(_run(args)))
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
