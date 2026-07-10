"""Text normalization helpers for deterministic ranking."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

_WORD_PATTERN = re.compile(r"[A-Za-z0-9_'-]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "can",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "you",
        "your",
    }
)


def normalize_text(text: str) -> str:
    """Collapse whitespace and normalize text for comparisons."""

    return _WHITESPACE_PATTERN.sub(" ", text or "").strip().lower()


def tokenize(text: str, *, remove_stop_words: bool = True) -> list[str]:
    """Tokenize text into normalized alphanumeric terms."""

    tokens = [
        match.group(0).lower()
        for match in _WORD_PATTERN.finditer(text or "")
    ]

    if not remove_stop_words:
        return tokens

    return [token for token in tokens if token not in _STOP_WORDS]


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


def jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)

    if not left_set or not right_set:
        return 0.0

    union = left_set | right_set

    if not union:
        return 0.0

    return len(left_set & right_set) / len(union)


def text_fingerprint(text: str) -> str:
    """Return a stable fingerprint for normalized text."""

    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
