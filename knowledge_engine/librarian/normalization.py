from __future__ import annotations

import re


def normalize_title(title: str | None) -> str:
    if not title:
        return ""

    text = title.lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\([^\)]*\)", " ", text)
    text = re.sub(r"\b(pdf|epub|docx|html|website archive)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def canonical_key(title: str | None, subject: str | None, resource_type: str | None) -> str:
    parts = [
        normalize_title(title),
        (subject or "unknown").lower().strip(),
        (resource_type or "unknown").lower().strip(),
    ]
    return "::".join(parts)
