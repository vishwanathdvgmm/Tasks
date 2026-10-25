from dataclasses import dataclass

@dataclass(frozen=True)
class Document:
    external_id: str
    title: str
    content: str
    tenant_id: str = "org_demo"

@dataclass
class SearchResult:
    external_id: str
    title: str
    content: str
    score: float
    source: str
