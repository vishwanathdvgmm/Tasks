"""Conservative regex PII redaction for common formats; not a complete PII detector."""
import re

_PATTERNS = [
    ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3,5}\)?[\s.-]?)\d{3,5}[\s.-]?\d{3,5}(?!\w)")),
    # Aadhaar-shaped 12-digit sequence with optional spaces/hyphens. Shape matching is not validation.
    ("AADHAAR", re.compile(r"(?<!\d)(?:\d{4}[\s-]?){2}\d{4}(?!\d)")),
    ("SSN", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")),
]

def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """Replace matched values with typed placeholders and return counts, never matched values."""
    counts: dict[str, int] = {}
    result = text
    for label, pattern in _PATTERNS:
        counter = 0

        def replacement(_match: re.Match[str], current_label: str = label) -> str:
            nonlocal counter
            counter += 1
            return f"<{current_label}_{counter}>"

        result = pattern.sub(replacement, result)
        if counter:
            counts[label] = counter
    return result, counts
