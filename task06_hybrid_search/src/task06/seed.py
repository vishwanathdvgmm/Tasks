from .db import connect, initialize_schema
from .embeddings import embed_texts
from .models import Document

DEMO_DOCUMENTS = [
    Document("err-5034", "ERR-5034 gateway timeout", "Error ERR-5034 occurs when the API gateway times out waiting for an upstream service. Check upstream latency, gateway timeout configuration, and service health."),
    Document("sku-xj-204", "SKU XJ-204 replacement battery", "Product SKU XJ-204 is a replacement lithium battery for the handheld scanner. Verify the SKU exactly before ordering parts."),
    Document("clause-9-2", "Legal clause 9.2 data retention", "Clause 9.2 specifies that customer records must be retained for seven years unless a shorter period is required by applicable law."),
    Document("vector-search", "Semantic vector search", "Dense retrieval embeds queries and documents in a vector space and ranks candidates by cosine similarity. It is useful for conceptual matches."),
    Document("full-text", "PostgreSQL full-text search", "PostgreSQL full-text search uses tsvector, tsquery, and ranking functions to retrieve documents containing matching terms."),
    Document("rrf", "Reciprocal Rank Fusion", "RRF merges ranked results from multiple retrieval systems using the reciprocal of a constant plus each document rank."),
    Document("cross-encoder", "Cross-encoder reranking", "A cross-encoder jointly evaluates a query and a candidate document, usually improving relevance ordering at higher inference cost."),
    Document("incident-5034", "Incident report: ERR-5034", "The incident identified repeated ERR-5034 responses after an upstream deployment. Rollback and connection pool checks resolved the issue."),
]

def seed_documents(tenant_id: str = "org_demo") -> int:
    initialize_schema()
    docs = [Document(d.external_id, d.title, d.content, tenant_id) for d in DEMO_DOCUMENTS]
    vectors = embed_texts([f"{d.title}\n{d.content}" for d in docs])
    with connect() as conn:
        for doc, vector in zip(docs, vectors):
            conn.execute(
                """INSERT INTO documents (tenant_id, external_id, title, content, embedding)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (tenant_id, external_id) DO UPDATE SET
                     title = EXCLUDED.title, content = EXCLUDED.content,
                     embedding = EXCLUDED.embedding""",
                (doc.tenant_id, doc.external_id, doc.title, doc.content, vector),
            )
    return len(docs)
