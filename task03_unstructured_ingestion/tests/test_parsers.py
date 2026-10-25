from pathlib import Path

from task03_ingestion.parsers import parse_file

def test_markdown_parser(tmp_path: Path):
    file = tmp_path / "guide.md"
    file.write_text("# Setup\n\nInstall the package.", encoding="utf-8")
    records = parse_file(file)
    assert len(records) == 1
    assert "# Setup" in records[0].text
    assert records[0].source_filename == "guide.md"

def test_html_parser_removes_script(tmp_path: Path):
    file = tmp_path / "page.html"
    file.write_text("<html><head><title>Guide</title></head><body><p>Hello</p>"
                    "<script>bad()</script></body></html>", encoding="utf-8")
    record = parse_file(file)[0]
    assert "Hello" in record.text
    assert "bad()" not in record.text
