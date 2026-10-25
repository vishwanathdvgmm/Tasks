from __future__ import annotations

import argparse
import json
from rich import print
from .config import settings
from .embeddings import demo_embedding
from .repository import PgVectorRepository
from .chroma_store import ChromaStore
from .benchmark import benchmark_search

SAMPLES = [
    ("doc-1", "PostgreSQL supports transactions and relational joins.", {"topic": "database"}),
    ("doc-2", "HNSW is a graph-based approximate nearest neighbor index.", {"topic": "indexing"}),
    ("doc-3", "IVFFlat partitions vectors into lists around centroids.", {"topic": "indexing"}),
    ("doc-4", "Tenant filters are essential for multi-tenant data isolation.", {"topic": "security"}),
]

def build_parser():
    parser = argparse.ArgumentParser(description="Task 05 vector database engineering lab")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="check PostgreSQL connectivity")
    seed = sub.add_parser("seed", help="insert demo rows into PostgreSQL")
    seed.add_argument("--tenant", default="org_demo")
    search = sub.add_parser("search", help="search PostgreSQL within a tenant")
    search.add_argument("query")
    search.add_argument("--tenant", default="org_demo")
    search.add_argument("--limit", type=int, default=3)
    search.add_argument("--metric", choices=["cosine", "l2", "inner_product"], default="cosine")
    index = sub.add_parser("index", help="create HNSW or IVFFlat ANN index")
    index.add_argument("kind", choices=["hnsw", "ivfflat"])
    index.add_argument("--lists", type=int, default=100)
    bench = sub.add_parser("benchmark", help="benchmark a PostgreSQL search")
    bench.add_argument("--tenant", default="org_demo")
    bench.add_argument("--iterations", type=int, default=30)
    chroma_seed = sub.add_parser("chroma-seed", help="seed embedded ChromaDB")
    chroma_seed.add_argument("--tenant", default="org_demo")
    chroma_search = sub.add_parser("chroma-search", help="search embedded ChromaDB")
    chroma_search.add_argument("query")
    chroma_search.add_argument("--tenant", default="org_demo")
    return parser

def main():
    args = build_parser().parse_args()
    repo = PgVectorRepository(settings.postgres_dsn, settings.vector_dimensions)
    if args.command == "check":
        repo.ping()
        print("[green]PostgreSQL connection OK[/green]")
    elif args.command == "seed":
        for external_id, content, metadata in SAMPLES:
            repo.upsert(args.tenant, external_id, content,
                        demo_embedding(content, settings.vector_dimensions), metadata)
        print(f"[green]Seeded {len(SAMPLES)} PostgreSQL demo documents for tenant {args.tenant}[/green]")
    elif args.command == "search":
        results = repo.search(args.tenant, demo_embedding(args.query, settings.vector_dimensions),
                              args.limit, metric=args.metric)
        print(json.dumps(results, indent=2, default=str))
    elif args.command == "index":
        repo.create_ann_index(args.kind, lists=args.lists)
        print(f"[green]Created {args.kind} index[/green]")
    elif args.command == "benchmark":
        query_vec = demo_embedding("nearest neighbor index", settings.vector_dimensions)
        stats = benchmark_search(lambda: repo.search(args.tenant, query_vec, limit=5),
                                 args.iterations)
        print(json.dumps(stats, indent=2))
    elif args.command == "chroma-seed":
        store = ChromaStore(settings.chroma_path)
        for external_id, content, metadata in SAMPLES:
            store.upsert(args.tenant, external_id, content,
                         demo_embedding(content, settings.vector_dimensions), metadata)
        print(f"[green]Seeded ChromaDB for tenant {args.tenant}[/green]")
    elif args.command == "chroma-search":
        store = ChromaStore(settings.chroma_path)
        print(json.dumps(store.search(args.tenant,
              demo_embedding(args.query, settings.vector_dimensions)), indent=2, default=str))

if __name__ == "__main__":
    main()
