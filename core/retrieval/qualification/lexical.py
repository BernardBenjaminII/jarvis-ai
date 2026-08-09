from __future__ import annotations

import math
import re
from dataclasses import dataclass


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+#.:-]*")

STOP_WORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "explain",
        "for", "from", "how", "in", "is", "it", "of", "on", "or",
        "that", "the", "this", "to", "was", "what", "when", "where",
        "which", "who", "why", "with",
    }
)

TECHNICAL_PATTERNS = (
    (
        re.compile(r"\(\s*(sha|aes)\s*\)\s*[- ]?\s*([0-9]{3,})", re.I),
        lambda m: f"{m.group(1)}{m.group(2)}",
    ),
    (
        re.compile(r"\b(sha|aes)\s*[- ]?\s*([0-9]{3,})\b", re.I),
        lambda m: f"{m.group(1)}{m.group(2)}",
    ),
    (
        re.compile(r"\b(rfc)\s*[- ]?\s*([0-9]{3,})\b", re.I),
        lambda m: f"{m.group(1)}{m.group(2)}",
    ),
    (
        re.compile(
            r"\b(cve)\s*[- ]?\s*([0-9]{4})\s*[- ]?\s*([0-9]{4,})\b",
            re.I,
        ),
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}",
    ),
    (
        re.compile(r"\b_?bitint\s*\(\s*([0-9]+)\s*\)", re.I),
        lambda m: f"bitint{m.group(1)}",
    ),
    (
        re.compile(r"\bc\s*\+\s*\+\b", re.I),
        lambda m: "c++",
    ),
    (
        re.compile(r"\bc\s*#\b", re.I),
        lambda m: "c#",
    ),
    (
        re.compile(r"\bc\s+plus\s+plus\b", re.I),
        lambda m: "c++",
    ),
    (
        re.compile(r"\bc\s+sharp\b", re.I),
        lambda m: "c#",
    ),
)


@dataclass(frozen=True, slots=True)
class LexicalAnalysis:
    score: float
    query_tokens: tuple[str, ...]
    candidate_tokens: tuple[str, ...]
    matched_tokens: tuple[str, ...]
    unique_coverage: float
    weighted_coverage: float


def normalize_text(text: str) -> str:
    value = text or ""
    value = value.replace("–", "-").replace("—", "-")

    for pattern, replacement in TECHNICAL_PATTERNS:
        value = pattern.sub(replacement, value)

    return value


def canonicalize_token(token: str) -> str:
    value = token.casefold().strip("._:-")

    if value in {"c++", "c#"}:
        return value

    return value


def tokenize(text: str) -> tuple[str, ...]:
    normalized = normalize_text(text)

    return tuple(
        token
        for raw in TOKEN_RE.findall(normalized)
        if (token := canonicalize_token(raw))
        and token not in STOP_WORDS
    )


def analyze_lexical(query: str, candidate_text: str) -> LexicalAnalysis:
    query_tokens = tokenize(query)
    candidate_tokens = tokenize(candidate_text)

    if not query_tokens or not candidate_tokens:
        return LexicalAnalysis(
            0.0,
            query_tokens,
            candidate_tokens,
            (),
            0.0,
            0.0,
        )

    unique_query = tuple(dict.fromkeys(query_tokens))
    candidate_set = set(candidate_tokens)
    matched = tuple(token for token in unique_query if token in candidate_set)

    unique_coverage = len(matched) / len(unique_query)

    weights = {
        token: 1.0 + math.log2(max(1, len(token)))
        for token in unique_query
    }

    weighted_coverage = (
        sum(weights[token] for token in matched)
        / (sum(weights.values()) or 1.0)
    )

    score = 0.5 * unique_coverage + 0.5 * weighted_coverage

    return LexicalAnalysis(
        max(0.0, min(1.0, score)),
        query_tokens,
        candidate_tokens,
        matched,
        unique_coverage,
        weighted_coverage,
    )
