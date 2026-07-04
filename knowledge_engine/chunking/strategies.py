from __future__ import annotations

import re


def chunk_text(
    text: str,
    max_chars: int = 2400,
    overlap: int = 250,
) -> list[str]:
    text = text.strip()

    if not text:
        return []

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n+", text)
        if p.strip()
    ]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue

        candidate = current + "\n\n" + paragraph

        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current.strip())
            tail = current[-overlap:] if overlap > 0 else ""
            current = (tail + "\n\n" + paragraph).strip()

    if current:
        chunks.append(current.strip())

    return chunks
