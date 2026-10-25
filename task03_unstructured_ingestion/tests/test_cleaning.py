from task03_ingestion.cleaning import clean_text

def test_clean_text_normalizes_whitespace_and_duplicate_lines():
    assert clean_text("A\u00a0  line\r\nA line\r\n\r\nB\u200b") == "A line\n\nB"
