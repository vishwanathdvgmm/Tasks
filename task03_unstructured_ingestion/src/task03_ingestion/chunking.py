from __future__ import annotations

import re
from collections.abc import Callable

from .tokenization import TokenCounter

def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

def recursive_chunks(text: str, counter: TokenCounter, max_tokens: int,
                     overlap_tokens: int = 0) -> list[str]:
    """Split on progressively weaker natural boundaries, then enforce a hard token cap."""
    if max_tokens < 1:
        raise ValueError("max_tokens must be >= 1")
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks: list[str] = []
    current = ""

    def emit_piece(piece: str) -> list[str]:
        if counter.count(piece) <= max_tokens:
            return [piece] if piece.strip() else []
        for sep in separators:
            if sep and sep in piece:
                pieces = [x for x in piece.split(sep) if x.strip()]
                if len(pieces) > 1:
                    out: list[str] = []
                    for item in pieces:
                        out.extend(emit_piece(item))
                    return out
        return counter.split_to_budget(piece, max_tokens)

    for para in _paragraphs(text):
        candidate = f"{current}\n\n{para}".strip() if current else para
        if counter.count(candidate) <= max_tokens:
            current = candidate
            continue
        if current:
            chunks.extend(emit_piece(current))
        current = ""
        pieces = emit_piece(para)
        for piece in pieces:
            if counter.count(piece) <= max_tokens:
                if current and counter.count(current + "\n\n" + piece) <= max_tokens:
                    current += "\n\n" + piece
                else:
                    if current:
                        chunks.append(current)
                    current = piece
            else:
                chunks.append(piece)
    if current:
        chunks.extend(emit_piece(current))

    if overlap_tokens > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for chunk in chunks[1:]:
            previous_ids = counter.encoding.encode(overlapped[-1])
            overlap = counter.encoding.decode(previous_ids[-overlap_tokens:]) if previous_ids else ""
            merged = (overlap + "\n" + chunk).strip()
            # Keep the hard cap: if overlap would exceed budget, emit original chunk.
            overlapped.append(merged if counter.count(merged) <= max_tokens else chunk)
        chunks = overlapped
    return [c for c in chunks if c.strip()]

def sliding_window_chunks(text: str, counter: TokenCounter, max_tokens: int,
                          overlap_tokens: int = 50) -> list[str]:
    if max_tokens < 1:
        raise ValueError("max_tokens must be >= 1")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be >= 0 and smaller than max_tokens")
    ids = counter.encoding.encode(text)
    step = max_tokens - overlap_tokens
    return [counter.encoding.decode(ids[i:i + max_tokens])
            for i in range(0, len(ids), step) if ids[i:i + max_tokens]]

def markdown_header_chunks(text: str, counter: TokenCounter, max_tokens: int,
                           overlap_tokens: int = 0) -> list[tuple[str | None, str]]:
    """Return (heading path, text) chunks; oversized sections are split recursively."""
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    sections: list[tuple[str | None, list[str]]] = []
    heading_stack: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            heading = " > ".join(heading_stack) if heading_stack else None
            sections.append((heading, current_lines.copy()))
            current_lines.clear()

    for line in text.splitlines():
        match = heading_re.match(line)
        if match:
            flush()
            level, title = len(match.group(1)), match.group(2).strip()
            heading_stack[:] = heading_stack[:level - 1]
            heading_stack.append(title)
            current_lines.append(line)
        else:
            current_lines.append(line)
    flush()

    output: list[tuple[str | None, str]] = []
    for heading, lines in sections:
        section_text = "\n".join(lines).strip()
        if not section_text:
            continue
        if counter.count(section_text) <= max_tokens:
            output.append((heading, section_text))
        else:
            output.extend((heading, c) for c in recursive_chunks(
                section_text, counter, max_tokens, overlap_tokens))
    return output

def _sentences(text: str) -> list[str]:
    # Lightweight sentence boundary heuristic; production use should account for abbreviations.
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]

def _terms(text: str) -> set[str]:
    return set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))

def _jaccard(a: str, b: str) -> float:
    ta, tb = _terms(a), _terms(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def semantic_chunks(text: str, counter: TokenCounter, max_tokens: int,
                    overlap_tokens: int = 0, similarity_threshold: float = 0.12
                    ) -> list[str]:
    """Offline lexical semantic baseline; low adjacent sentence similarity creates boundaries."""
    sentences = _sentences(text)
    if not sentences:
        return []
    groups: list[str] = []
    current = sentences[0]
    for sentence in sentences[1:]:
        similarity = _jaccard(current[-500:], sentence)
        candidate = current + " " + sentence
        if similarity < similarity_threshold or counter.count(candidate) > max_tokens:
            groups.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        groups.append(current)

    final: list[str] = []
    for group in groups:
        final.extend(recursive_chunks(group, counter, max_tokens, overlap_tokens))
    return final

def chunk_text(text: str, strategy: str, counter: TokenCounter, max_tokens: int,
               overlap_tokens: int = 50) -> list[tuple[str | None, str]]:
    if strategy == "recursive":
        return [(None, c) for c in recursive_chunks(text, counter, max_tokens, overlap_tokens)]
    if strategy == "sliding":
        return [(None, c) for c in sliding_window_chunks(text, counter, max_tokens, overlap_tokens)]
    if strategy == "markdown":
        return markdown_header_chunks(text, counter, max_tokens, overlap_tokens)
    if strategy == "semantic":
        return [(None, c) for c in semantic_chunks(text, counter, max_tokens, overlap_tokens)]
    raise ValueError(f"Unknown strategy: {strategy}")
