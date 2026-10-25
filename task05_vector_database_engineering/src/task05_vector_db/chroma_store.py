from __future__ import annotations

from typing import Any
import chromadb

class ChromaStore:
    """Embedded ChromaDB collection wrapper with tenant metadata filtering."""

    def __init__(self, path: str = "./.chroma", collection_name: str = "task05_documents"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(
        self, tenant_id: str, external_id: str, content: str,
        embedding: list[float], metadata: dict[str, Any] | None = None,
    ) -> None:
        if not tenant_id.strip():
            raise ValueError("tenant_id must not be empty")
        safe_metadata = dict(metadata or {})
        # Keep tenant_id as a first-class filterable metadata field.
        safe_metadata["tenant_id"] = tenant_id
        self.collection.upsert(
            ids=[f"{tenant_id}:{external_id}"],
            documents=[content],
            embeddings=[embedding],
            metadatas=[safe_metadata],
        )

    def search(self, tenant_id: str, query_embedding: list[float], limit: int = 5):
        if not tenant_id.strip():
            raise ValueError("tenant_id must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"tenant_id": tenant_id},
            include=["documents", "metadatas", "distances"],
        )
