from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
}


def normalize_text(value: str) -> str:
    tokens = [token for token in _TOKEN_RE.findall(value.lower()) if token not in _STOPWORDS]
    return " ".join(tokens)


def token_set(value: str) -> frozenset[str]:
    return frozenset(normalize_text(value).split())


def jaccard(left: str, right: str) -> float:
    a = token_set(left)
    b = token_set(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def polarity(value: str) -> int:
    lowered = value.lower()
    negative_markers = (
        "must not", "shall not", "should not", "may not", "never", "prohibited",
        "forbidden", "cannot", "mustn't", "shalln't",
    )
    return -1 if any(marker in lowered for marker in negative_markers) else 1
