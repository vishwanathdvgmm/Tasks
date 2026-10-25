# Task 03 — Unstructured Data Ingestion & Text Chunking

A runnable, local-first document ingestion pipeline for PDF, Markdown, DOCX, and HTML. It extracts text and basic metadata, normalizes noisy text, applies four chunking strategies, measures chunk sizes with `tiktoken`, and exports JSONL records.

## Features

- **Parsers:** digital PDFs and page metadata via PyMuPDF; Markdown and plain text; Word DOCX; HTML.
- **Scanned PDFs:** optional OCR using Tesseract (`uv sync --extra ocr` plus a system Tesseract installation).
- **Cleaning:** Unicode NFC normalization, whitespace cleanup, duplicate adjacent line removal, and line-break normalization.
- **Tables:** best-effort PDF table extraction into Markdown; HTML tables are retained as Markdown-like pipe rows.
- **Chunking:** recursive character splitting, sliding-window splitting, Markdown header splitting, and offline lexical semantic splitting.
- **Token budgets:** `tiktoken` (`cl100k_base` by default) measures each output chunk. The engine recursively subdivides any chunk over the configured token cap.
- **Metadata:** source filename/path, page number where available, section heading, author where available, document creation timestamp when available, ingestion timestamp, strategy, token count, and stable chunk ID.
- **Benchmark:** run all chunking methods against a document and compare chunk count, token distribution, and elapsed time.
- **Tests:** focused parser, cleaning, chunking, token-budget, and CLI tests.

## Quick start (using uv)

Install `uv` if it is not already installed: https://docs.astral.sh/uv/

```bash
uv sync --extra dev
uv run task03 ingest ./data --output ./output/chunks.jsonl --strategy recursive --chunk-tokens 500 --overlap-tokens 60
uv run task03 benchmark ./data --output ./output/benchmark.json
uv run pytest
```

`./data` can contain nested folders. Supported extensions: `.pdf`, `.md`, `.markdown`, `.txt`, `.docx`, `.html`, `.htm`.

To try the included examples:

```bash
uv run task03 ingest ./data --output ./output/chunks.jsonl
uv run task03 benchmark ./data
```

## Optional OCR for scanned PDFs

Install the Tesseract executable for your operating system, then:

```bash
uv sync --extra dev --extra ocr
uv run task03 ingest ./scanned_docs --ocr
```

OCR is attempted only when a PDF page has little or no extractable text. OCR is optional because the Tesseract binary is a separate system dependency. Without OCR enabled, a scanned page is emitted with a warning if no digital text is found.

## CLI

```text
task03 ingest PATH [--output PATH] [--strategy recursive|sliding|markdown|semantic]
                 [--chunk-tokens N] [--overlap-tokens N] [--encoding NAME] [--ocr]
task03 benchmark PATH [--output PATH] [--chunk-tokens N] [--overlap-tokens N]
```

- `PATH` may be one file or a directory.
- `--chunk-tokens` is a hard upper bound for each chunk's measured token count.
- `--overlap-tokens` applies to the sliding-window strategy. For recursive splitting it is used as a best-effort character overlap.
- `--encoding` defaults to `cl100k_base`. Choose the encoding appropriate for the downstream model; token counts are tokenizer-specific.
- JSONL output contains one chunk object per line.

## Architecture

```text
src/task03_ingestion/
  models.py       typed document and chunk records
  parsers.py      file-type adapters
  cleaning.py     deterministic text normalization
  tokenization.py tiktoken wrapper and hard-budget enforcement
  chunking.py     four chunking strategies
  pipeline.py     ETL orchestration and metadata enrichment
  benchmark.py    comparative metrics
  cli.py          command-line interface
```

## Chunking strategies and trade-offs

| Strategy                    | How it works                                                                 | Strength                                             | Limitation                                                                |
| --------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------- |
| Recursive character         | Tries paragraph, line, sentence, then word boundaries                        | Strong default; preserves natural boundaries         | Character separators are only proxies for semantic units                  |
| Sliding window              | Moves through text with a configured overlap                                 | Reduces boundary fragmentation                       | More duplicate text and storage                                           |
| Markdown headers            | Groups content under heading hierarchy, then token-splits oversized sections | Preserves section context                            | Best for structured Markdown; large sections still need subdivision       |
| Semantic (offline baseline) | Groups sentences based on lexical Jaccard similarity                         | No embedding API/key required; useful for a baseline | Not embedding-based semantic chunking; misses synonymy and deeper meaning |

## Engineering notes

- **Exact token counts are tokenizer-specific.** `tiktoken` reports counts for the configured encoding, not a universal token count for every model.
- **Scanned PDF OCR is not automatic by default.** Enable `--ocr` and install both the Python extra and system Tesseract.
- **PDF table extraction is best-effort.** Complex merged cells, multi-page tables, and low-quality scans need validation. HTML table rows are flattened with headers kept nearby.
- **Creation time:** the pipeline uses embedded document metadata when available. Filesystem modification time is not falsely labelled as document creation time; ingestion time is always recorded separately.
- **Semantic chunking:** this project intentionally uses an offline lexical baseline so the project runs without API keys. For production RAG, replace the similarity function with embedding-based boundary detection and evaluate retrieval quality on a labelled query set.

## Example output

Each JSONL row resembles:

```json
{
  "chunk_id": "sha256-prefix",
  "text": "The chunk text...",
  "token_count": 123,
  "metadata": {
    "source_filename": "guide.md",
    "source_path": "data/guide.md",
    "page_number": null,
    "section_header": "Installation",
    "author": null,
    "document_created_at": null,
    "ingested_at": "2026-01-01T12:00:00+00:00",
    "chunk_index": 0,
    "strategy": "recursive"
  }
}
```

## Suggested assignment demo

1. Run `uv run pytest`.
2. Ingest the sample `data/employee_handbook.md`.
3. Compare `recursive`, `sliding`, `markdown`, and `semantic` outputs.
4. Run `benchmark` and explain why chunk count, overlap, and token distributions differ.
5. Explain why the semantic method is a lexical baseline and how embeddings would improve it.
