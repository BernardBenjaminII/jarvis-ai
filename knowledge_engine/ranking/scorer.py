"""Explainable scoring functions for JARVIS knowledge candidates."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

from knowledge_engine.ranking.models import (
    RankingBreakdown,
    RankingCandidate,
    RankingWeights,
)
from knowledge_engine.ranking.text import jaccard_similarity, token_set


_AUTHORITY_BY_SUFFIX = {
    ".md": 0.84,
    ".rst": 0.82,
    ".txt": 0.68,
    ".pdf": 0.78,
    ".epub": 0.76,
    ".docx": 0.74,
    ".odt": 0.72,
    ".html": 0.65,
    ".htm": 0.65,
    ".json": 0.60,
    ".yaml": 0.60,
    ".yml": 0.60,
    ".py": 0.88,
    ".rs": 0.88,
    ".java": 0.86,
    ".cpp": 0.86,
    ".c": 0.86,
    ".h": 0.84,
    ".sh": 0.82,
    ".ps1": 0.82,
}

_LOW_AUTHORITY_PATH_TERMS = {
    "cache",
    "temp",
    "tmp",
    "backup",
    "backups",
    "archive",
    "downloads",
}

_HIGH_AUTHORITY_PATH_TERMS = {
    "docs",
    "documentation",
    "manual",
    "reference",
    "standards",
    "official",
    "source",
    "src",
}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def lexical_score(query: str, text: str) -> float:
    query_tokens = token_set(query)
    text_tokens = token_set(text)

    if not query_tokens or not text_tokens:
        return 0.0

    query_coverage = len(query_tokens & text_tokens) / len(query_tokens)
    set_similarity = jaccard_similarity(query_tokens, text_tokens)

    return clamp((query_coverage * 0.75) + (set_similarity * 0.25))


def completeness_score(text: str) -> float:
    stripped = (text or "").strip()

    if not stripped:
        return 0.0

    character_count = len(stripped)
    word_count = len(stripped.split())

    character_component = min(character_count / 900.0, 1.0)
    word_component = min(word_count / 150.0, 1.0)

    sentence_ending_bonus = 1.0 if stripped[-1:] in ".!?:;)]}" else 0.55
    fragmentation_penalty = 0.65 if word_count < 20 else 1.0

    return clamp(
        (
            character_component * 0.45
            + word_component * 0.40
            + sentence_ending_bonus * 0.15
        )
        * fragmentation_penalty
    )


def authority_score(source: str) -> float:
    if not source:
        return 0.45

    path = Path(source)
    suffix = path.suffix.lower()

    score = _AUTHORITY_BY_SUFFIX.get(suffix, 0.58)
    path_terms = {part.lower() for part in path.parts}

    if path_terms & _HIGH_AUTHORITY_PATH_TERMS:
        score += 0.10

    if path_terms & _LOW_AUTHORITY_PATH_TERMS:
        score -= 0.16

    filename = path.name.lower()

    if any(term in filename for term in ("readme", "manual", "reference", "spec")):
        score += 0.06

    if any(term in filename for term in ("draft", "copy", "old", "backup")):
        score -= 0.10

    return clamp(score)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    cleaned = value.strip()

    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def freshness_score(
    created_at: str | None,
    updated_at: str | None,
    *,
    now: datetime | None = None,
) -> float:
    timestamp = _parse_timestamp(updated_at) or _parse_timestamp(created_at)

    if timestamp is None:
        return 0.50

    current = now or datetime.now(UTC)
    age_days = max((current - timestamp).total_seconds() / 86400.0, 0.0)

    # Half-life style decay with a stable floor for historical references.
    decay = math.exp(-age_days / 1825.0)
    return clamp(0.25 + (0.75 * decay))


def diversity_score(candidate: RankingCandidate) -> float:
    """
    Initial diversity estimate.

    Final source repetition is handled by the ranker. This component rewards
    candidates with usable source identity and chunk location metadata.
    """

    score = 0.45

    if candidate.source:
        score += 0.35

    if candidate.chunk_index is not None:
        score += 0.20

    return clamp(score)


def calculate_breakdown(
    *,
    query: str,
    candidate: RankingCandidate,
    weights: RankingWeights,
    duplicate_penalty: float = 0.0,
) -> RankingBreakdown:
    semantic = clamp(candidate.semantic_score)
    lexical = lexical_score(query, candidate.text)
    quality = clamp(candidate.quality_score)
    authority = authority_score(candidate.source)
    completeness = completeness_score(candidate.text)
    freshness = freshness_score(
        candidate.created_at,
        candidate.updated_at,
    )
    diversity = diversity_score(candidate)

    weighted_score = (
        semantic * weights.semantic
        + lexical * weights.lexical
        + quality * weights.quality
        + authority * weights.authority
        + completeness * weights.completeness
        + freshness * weights.freshness
        + diversity * weights.diversity
    )

    final_score = clamp(weighted_score - clamp(duplicate_penalty))

    return RankingBreakdown(
        semantic=semantic,
        lexical=lexical,
        quality=quality,
        authority=authority,
        completeness=completeness,
        freshness=freshness,
        diversity=diversity,
        duplicate_penalty=clamp(duplicate_penalty),
        final_score=final_score,
    )
