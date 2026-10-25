from .models import RetrievedChunk

def assemble_context(chunks: list[RetrievedChunk]) -> str:
    """Put strongest evidence first and preserve explicit source boundaries."""
    blocks = []
    for chunk in chunks:
        metadata = ", ".join(f"{k}={v}" for k, v in sorted(chunk.metadata.items())) or "none"
        blocks.append(
            f"[SOURCE chunk_id={chunk.chunk_id} file={chunk.source_filename} page={chunk.page_number} metadata={metadata}]\n"
            f"{chunk.text}\n[END SOURCE {chunk.chunk_id}]"
        )
    # Best chunks at the top; in production, a context-position strategy can also
    # place the strongest remaining evidence at the end to mitigate lost-in-middle.
    return "\n\n".join(blocks)
