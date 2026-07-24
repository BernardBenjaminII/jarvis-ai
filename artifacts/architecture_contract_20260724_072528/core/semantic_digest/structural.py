from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


HEADING_RE = re.compile(r"^(chapter\s+\d+|section\s+\d+|\d+(\.\d+)*\s+.+|[A-Z][A-Z0-9 ,:/()\-]{8,})$", re.I)


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def extract_headings(text: str, limit: int = 80) -> list[str]:
    headings: list[str] = []

    for raw in text.splitlines():
        line = clean_line(raw)

        if not line or len(line) > 140:
            continue

        if HEADING_RE.match(line):
            headings.append(line)

        if len(headings) >= limit:
            break

    return headings


def extract_terms(text: str, limit: int = 80) -> list[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{4,}\b", text.lower())

    stop = {
        "about", "after", "again", "being", "could", "every", "first", "found",
        "general", "other", "should", "their", "there", "these", "those",
        "through", "using", "where", "which", "while", "would", "figure",
        "table", "chapter", "section", "pages", "manual", "edition",
    }

    counts = Counter(w for w in words if w not in stop)
    return [word for word, _ in counts.most_common(limit)]


def extract_structure(path: Path, text: str) -> dict:
    headings = extract_headings(text)
    terms = extract_terms(text)

    return {
        "title": path.stem.replace("_", " ").replace("-", " ").strip(),
        "headings": headings,
        "terms": terms,
        "content_chars": len(text),
    }
