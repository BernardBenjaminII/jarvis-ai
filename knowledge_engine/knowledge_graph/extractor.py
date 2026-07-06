from __future__ import annotations

import re


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "your",
    "files", "file", "book", "archive", "website", "document", "media",
    "abdullah", "jarvisdata", "knowledge", "xfer", "staged", "ebooks",
}


ENTITY_PATTERNS: dict[str, list[str]] = {
    "topic": [
        "programming", "security", "history", "religion", "aviation",
        "cybersecurity", "military_history", "academic",
    ],
    "technology": [
        "cmake", "python", "java", "javascript", "linux", "sql", "c++",
        "cpp", "rust", "bash", "faiss",
    ],
    "place": [
        "afghanistan", "kabul", "iraq", "morocco", "germany",
    ],
    "organization": [
        "wikileaks", "faa", "nasa", "us army",
    ],
    "work": [
        "quran", "kabul war diary", "afghanistan war diary",
        "effective c",
    ],
}


def canonicalize(text: str) -> str:
    text = text.lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9+ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_named_entities(*texts: str | None) -> list[tuple[str, str, float]]:
    haystack = " ".join(t or "" for t in texts)
    canonical_haystack = f" {canonicalize(haystack)} "

    found: list[tuple[str, str, float]] = []

    for entity_type, names in ENTITY_PATTERNS.items():
        for name in names:
            c = canonicalize(name)
            if f" {c} " in canonical_haystack:
                found.append((entity_type, name, 0.85))

    # Simple title-case phrase extraction for future growth.
    raw = " ".join(t or "" for t in texts)
    for phrase in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", raw):
        c = canonicalize(phrase)
        if c and c not in STOPWORDS and len(c) > 4:
            found.append(("entity", phrase, 0.55))

    unique: dict[tuple[str, str], tuple[str, str, float]] = {}
    for entity_type, name, confidence in found:
        key = (entity_type, canonicalize(name))
        current = unique.get(key)
        if current is None or confidence > current[2]:
            unique[key] = (entity_type, name, confidence)

    return sorted(unique.values(), key=lambda item: (item[0], item[1]))
