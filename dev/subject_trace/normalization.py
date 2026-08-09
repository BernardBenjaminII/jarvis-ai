from __future__ import annotations

import re
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9_+-]+")


def normalize_text(value: str) -> str:
    return " ".join(TOKEN_RE.findall((value or "").casefold()))


def tokens(value: str) -> tuple[str, ...]:
    return tuple(TOKEN_RE.findall((value or "").casefold()))


def normalize_subject(value: str) -> str:
    text = normalize_text(value).replace(" ", "_")
    return text.strip("_")


def normalize_subjects(values: Iterable[str]) -> tuple[str, ...]:
    result = []
    seen = set()

    for value in values:
        normalized = normalize_subject(str(value))
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return tuple(result)
