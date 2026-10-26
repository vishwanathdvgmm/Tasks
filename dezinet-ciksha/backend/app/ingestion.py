import re
from bs4 import BeautifulSoup
from pypdf import PdfReader
from io import BytesIO
from .config import CHUNK_SIZE, CHUNK_OVERLAP

def parse_file(filename: str, content_type: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf") or content_type == "application/pdf":
        reader = PdfReader(BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith((".html", ".htm")) or "html" in content_type:
        text = BeautifulSoup(data.decode("utf-8", errors="replace"), "html.parser").get_text(" ", strip=True)
    elif name.endswith((".md", ".markdown", ".txt")) or content_type.startswith("text/"):
        text = data.decode("utf-8", errors="replace")
    else:
        raise ValueError("Supported formats: PDF, Markdown, HTML, and plain text.")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_text(text: str) -> list[str]:
    # Recursive-style splitting: prefer paragraph, then line, then sentence, then spaces.
    separators = ["\n\n", "\n", ". ", " "]
    chunks, remaining = [], text.strip()
    while remaining:
        if len(remaining) <= CHUNK_SIZE:
            chunks.append(remaining)
            break
        cut = -1
        for sep in separators:
            candidate = remaining.rfind(sep, 0, CHUNK_SIZE)
            if candidate > CHUNK_SIZE // 3:
                cut = candidate + len(sep)
                break
        if cut < 1:
            cut = CHUNK_SIZE
        piece = remaining[:cut].strip()
        if piece:
            chunks.append(piece)
        remaining = remaining[max(1, cut - CHUNK_OVERLAP):].strip()
    return chunks
