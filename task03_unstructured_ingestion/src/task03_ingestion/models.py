from dataclasses import asdict, dataclass
from typing import Any

@dataclass
class DocumentRecord:
    text: str
    source_filename: str
    source_path: str
    page_number: int | None = None
    section_header: str | None = None
    author: str | None = None
    document_created_at: str | None = None
    extra: dict[str, Any] | None = None

@dataclass
class ChunkRecord:
    chunk_id: str
    text: str
    token_count: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
