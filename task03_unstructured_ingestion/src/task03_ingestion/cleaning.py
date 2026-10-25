import re
import unicodedata

def clean_text(text: str) -> str:
    """Normalize common extraction noise without aggressively rewriting content."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize horizontal whitespace, but preserve meaningful line boundaries.
    lines = [re.sub(r"[\t\f\v ]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    previous_nonempty = None
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if cleaned and blank_count <= 1:
                cleaned.append("")
            continue
        blank_count = 0
        # Remove only adjacent duplicate non-empty lines, a common PDF extraction artifact.
        if line == previous_nonempty:
            continue
        cleaned.append(line)
        previous_nonempty = line
    return "\n".join(cleaned).strip()
