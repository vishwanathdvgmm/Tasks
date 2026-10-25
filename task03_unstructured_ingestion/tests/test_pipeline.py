import json
from pathlib import Path

from task03_ingestion.pipeline import ingest, records_to_jsonl

def test_pipeline_writes_metadata_and_token_bounded_chunks(tmp_path: Path):
    file = tmp_path / "manual.md"
    file.write_text("# Install\n\n" + ("Install the application carefully. " * 100),
                    encoding="utf-8")
    records = ingest(file, strategy="markdown", max_tokens=30, overlap_tokens=3)
    assert records
    assert all(r.token_count <= 30 for r in records)
    assert records[0].metadata["source_filename"] == "manual.md"
    parsed = json.loads(records_to_jsonl(records).splitlines()[0])
    assert parsed["chunk_id"]
    assert parsed["metadata"]["strategy"] == "markdown"
