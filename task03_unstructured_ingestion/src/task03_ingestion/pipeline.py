from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Iterable

from .chunking import chunk_text
from .models import ChunkRecord, DocumentRecord
from .parsers import discover_files, parse_file
from .tokenization import TokenCounter

STRATEGIES = ("recursive", "sliding", "markdown", "semantic")

def ingest(path: Path, strategy: str = "recursive", max_tokens: int = 500,
           overlap_tokens: int = 50, encoding_name: str = "cl100k_base",
           ocr: bool = False) -> list[ChunkRecord]:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {', '.join(STRATEGIES)}")
    counter = TokenCounter(encoding_name)
    chunks: list[ChunkRecord] = []
    for file_path in discover_files(path):
        docs = parse_file(file_path, ocr=ocr)
        for doc in docs:
            if not doc.text.strip():
                continue
            for index, (section, chunk) in enumerate(
                chunk_text(doc.text, strategy, counter, max_tokens, overlap_tokens)
            ):
                token_count = counter.count(chunk)
                # Defensive assertion: never silently emit an over-budget chunk.
                if token_count > max_tokens:
                    raise RuntimeError(
                        f"Chunk budget exceeded ({token_count}>{max_tokens}) for {file_path}"
                    )
                metadata = {
                    "source_filename": doc.source_filename,
                    "source_path": doc.source_path,
                    "page_number": doc.page_number,
                    "section_header": section or doc.section_header,
                    "author": doc.author,
                    "document_created_at": doc.document_created_at,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "chunk_index": index,
                    "strategy": strategy,
                    "tokenizer": encoding_name,
                    **(doc.extra or {}),
                }
                stable = hashlib.sha256(
                    f"{doc.source_path}|{doc.page_number}|{strategy}|{index}|{chunk}".encode()
                ).hexdigest()[:20]
                chunks.append(ChunkRecord(stable, chunk, token_count, metadata))
    return chunks

def records_to_jsonl(records: Iterable[ChunkRecord]) -> str:
    import json
    return "\n".join(json.dumps(r.to_dict(), ensure_ascii=False) for r in records)
