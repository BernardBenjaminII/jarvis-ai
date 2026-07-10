"""Duplicate and near-duplicate detection for ranked knowledge."""

from __future__ import annotations

from knowledge_engine.ranking.models import RankingCandidate
from knowledge_engine.ranking.text import (
    jaccard_similarity,
    normalize_text,
    token_set,
)


def duplicate_similarity(
    left: RankingCandidate,
    right: RankingCandidate,
) -> float:
    left_text = normalize_text(left.text)
    right_text = normalize_text(right.text)

    if not left_text or not right_text:
        return 0.0

    if left_text == right_text:
        return 1.0

    left_tokens = token_set(left_text)
    right_tokens = token_set(right_text)

    token_similarity = jaccard_similarity(left_tokens, right_tokens)

    same_source = bool(left.source) and left.source == right.source

    adjacent_chunks = (
        same_source
        and left.chunk_index is not None
        and right.chunk_index is not None
        and abs(left.chunk_index - right.chunk_index) <= 1
    )

    if adjacent_chunks:
        token_similarity = min(1.0, token_similarity + 0.08)

    return token_similarity


def duplicate_penalty(
    candidate: RankingCandidate,
    selected: list[RankingCandidate],
    *,
    threshold: float = 0.82,
    maximum_penalty: float = 0.30,
) -> float:
    if not selected:
        return 0.0

    strongest_similarity = max(
        duplicate_similarity(candidate, existing)
        for existing in selected
    )

    if strongest_similarity < threshold:
        return 0.0

    similarity_range = max(1.0 - threshold, 1e-9)
    normalized = (strongest_similarity - threshold) / similarity_range

    return min(maximum_penalty, normalized * maximum_penalty)
