"""Command-line demo: uv run embeddings-demo."""
from __future__ import annotations
import argparse
import json
from .cache import MemoryCache
from .metrics import cosine_similarity, dot_product, euclidean_distance, l2_normalize
from .providers import MockEmbeddingProvider, OpenAIEmbeddingProvider, SentenceTransformersProvider
from .service import EmbeddingService

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate embeddings and compare vector metrics.")
    parser.add_argument("texts", nargs="*", default=["A cat sits on a mat.", "A dog runs in a park."])
    parser.add_argument("--provider", choices=("mock", "openai", "local"), default="mock")
    parser.add_argument("--model", default="BAAI/bge-small-en-v1.5", help="Local model name")
    parser.add_argument("--dimensions", type=int, default=32, help="Mock vector dimensions")
    args = parser.parse_args()

    if args.provider == "mock":
        provider = MockEmbeddingProvider(args.dimensions)
    elif args.provider == "openai":
        provider = OpenAIEmbeddingProvider()
    else:
        provider = SentenceTransformersProvider(args.model)

    service = EmbeddingService(provider, cache=MemoryCache())
    vectors = service.embed_texts(args.texts)
    print(json.dumps({
        "provider": provider.model_name,
        "dimensions": len(vectors[0]) if vectors else 0,
        "texts": args.texts,
        "vectors": vectors,
    }, indent=2))
    if len(vectors) >= 2:
        a, b = vectors[0], vectors[1]
        an, bn = l2_normalize(a), l2_normalize(b)
        print("\nSimilarity comparison:")
        print(f"cosine_similarity: {cosine_similarity(a, b):.6f}")
        print(f"dot_product:       {dot_product(a, b):.6f}")
        print(f"normalized dot:    {dot_product(an, bn):.6f}")
        print(f"euclidean_distance:{euclidean_distance(a, b):.6f}")

if __name__ == "__main__":
    main()
