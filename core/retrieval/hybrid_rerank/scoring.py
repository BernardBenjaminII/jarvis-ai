from __future__ import annotations

import math
from .dedup import normalize_text


def _contains(term: str, text: str) -> bool:
    return term in text


def lexical_component(terms: tuple[str, ...], text: str) -> tuple[float, tuple[str, ...]]:
    if not terms:
        return 0.0, tuple()

    n = normalize_text(text)
    matched = tuple(t for t in terms if _contains(t, n))
    coverage = len(matched) / len(terms)

    # Reward co-occurrence of multiple query terms within the same evidence span.
    proximity_bonus = 0.0
    if len(matched) >= 2:
        positions = []
        for t in matched:
            pos = n.find(t)
            if pos >= 0:
                positions.append(pos)
        if len(positions) >= 2:
            span = max(positions) - min(positions)
            proximity_bonus = max(0.0, 1.0 - min(span, 1200) / 1200.0) * 0.25

    return min(1.0, coverage + proximity_bonus), matched


def title_component(terms: tuple[str, ...], title: str) -> float:
    if not terms:
        return 0.0
    n = normalize_text(title)
    hits = sum(1 for t in terms if t in n)
    return hits / len(terms)


def hybrid_score(
    semantic: float,
    lexical: float,
    title: float,
    diversity_penalty: float,
) -> float:
    # Semantic remains primary, but lexical/title agreement can overturn
    # semantically-adjacent false positives such as generic iteration passages.
    score = (
        0.64 * float(semantic)
        + 0.24 * float(lexical)
        + 0.12 * float(title)
        - float(diversity_penalty)
    )
    return max(-1.0, min(1.0, score))
