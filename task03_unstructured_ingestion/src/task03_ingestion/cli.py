from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .benchmark import benchmark
from .pipeline import STRATEGIES, ingest, records_to_jsonl

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task03", description="Parse documents, clean text, chunk, and measure tokens."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_parser = sub.add_parser("ingest", help="Ingest files and write JSONL chunks.")
    ingest_parser.add_argument("path", type=Path)
    ingest_parser.add_argument("--output", type=Path, default=Path("output/chunks.jsonl"))
    ingest_parser.add_argument("--strategy", choices=STRATEGIES, default="recursive")
    ingest_parser.add_argument("--chunk-tokens", type=int, default=500)
    ingest_parser.add_argument("--overlap-tokens", type=int, default=50)
    ingest_parser.add_argument("--encoding", default="cl100k_base")
    ingest_parser.add_argument("--ocr", action="store_true")

    bench_parser = sub.add_parser("benchmark", help="Compare all four chunking strategies.")
    bench_parser.add_argument("path", type=Path)
    bench_parser.add_argument("--output", type=Path, default=Path("output/benchmark.json"))
    bench_parser.add_argument("--chunk-tokens", type=int, default=500)
    bench_parser.add_argument("--overlap-tokens", type=int, default=50)
    bench_parser.add_argument("--encoding", default="cl100k_base")
    bench_parser.add_argument("--ocr", action="store_true")
    return parser

def main() -> None:
    args = build_parser().parse_args()
    if not args.path.exists():
        print(f"Error: path does not exist: {args.path}", file=sys.stderr)
        raise SystemExit(2)
    if args.chunk_tokens < 1:
        print("Error: --chunk-tokens must be >= 1", file=sys.stderr)
        raise SystemExit(2)
    if args.overlap_tokens < 0:
        print("Error: --overlap-tokens must be >= 0", file=sys.stderr)
        raise SystemExit(2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.command == "ingest":
        records = ingest(args.path, args.strategy, args.chunk_tokens,
                         args.overlap_tokens, args.encoding, args.ocr)
        args.output.write_text(records_to_jsonl(records) + ("\n" if records else ""),
                                encoding="utf-8")
        print(f"Wrote {len(records)} chunks to {args.output}")
    else:
        report = benchmark(args.path, args.chunk_tokens, args.overlap_tokens,
                           args.encoding, args.ocr)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        print(f"\nSaved benchmark to {args.output}")

if __name__ == "__main__":
    main()
