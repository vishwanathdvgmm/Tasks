"""Heuristic prompt-injection screening. Do not treat this as a standalone security boundary."""
import re
from dataclasses import dataclass

_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\b(disregard|override|forget)\s+(all\s+)?(previous|prior|system|developer)\s+(instructions?|rules?|messages?)\b", re.IGNORECASE),
    re.compile(r"\b(reveal|print|show|dump|exfiltrate)\b.{0,50}\b(system prompt|hidden instructions|secrets|credentials|api keys)\b", re.IGNORECASE),
    re.compile(r"\b(jailbreak|DAN mode|developer mode)\b", re.IGNORECASE),
    re.compile(r"\bact as\b.{0,40}\b(no restrictions|unfiltered|without rules)\b", re.IGNORECASE),
]

@dataclass(frozen=True)
class InjectionVerdict:
    flagged: bool
    matched_categories: tuple[str, ...]

def inspect_user_input(text: str) -> InjectionVerdict:
    categories = []
    labels = ("instruction_override", "policy_override", "secret_extraction", "jailbreak_keyword", "roleplay_bypass")
    for label, pattern in zip(labels, _PATTERNS):
        if pattern.search(text):
            categories.append(label)
    return InjectionVerdict(bool(categories), tuple(categories))
