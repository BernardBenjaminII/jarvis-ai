"""Normalize heterogeneous retrieval results for ranking."""

from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from knowledge_engine.ranking.models import RankingCandidate, mapping_value


_TEXT_FIELDS = (
    "text",
    "content",
    "chunk_text",
    "body",
    "excerpt",
    "snippet",
)

_SOURCE_FIELDS = (
    "source",
    "source_path",
    "file",
    "file_path",
    "path",
    "document_path",
    "filename",
)

_CHUNK_FIELDS = (
    "chunk_index",
    "chunk_number",
    "chunk_id",
    "index",
)

_SCORE_FIELDS = (
    "score",
    "similarity",
    "similarity_score",
    "semantic_score",
    "relevance_score",
    "distance",
)

_QUALITY_FIELDS = (
    "quality",
    "quality_score",
    "document_quality",
)

_CREATED_FIELDS = (
    "created_at",
    "created",
    "ingested_at",
)

_UPDATED_FIELDS = (
    "updated_at",
    "modified_at",
    "modified",
    "mtime",
)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(number):
        return default

    return number


def normalize_semantic_score(raw_score: Any) -> float:
    """
    Normalize common similarity and distance representations to 0..1.

    Supported conventions:
    - cosine similarity in -1..1
    - similarity in 0..1
    - percentage in 0..100
    - non-negative distance, converted using 1 / (1 + distance)
    """

    score = safe_float(raw_score, 0.0)

    if -1.0 <= score < 0.0:
        return clamp((score + 1.0) / 2.0)

    if 0.0 <= score <= 1.0:
        return score

    if 1.0 < score <= 100.0:
        return clamp(score / 100.0)

    if score > 100.0:
        return 1.0 / (1.0 + score)

    return 0.0


def normalize_quality_score(raw_quality: Any) -> float:
    quality = safe_float(raw_quality, 0.0)

    if 0.0 <= quality <= 1.0:
        return quality

    if 1.0 < quality <= 100.0:
        return quality / 100.0

    return clamp(quality)


def _extract_metadata(result: Any) -> dict[str, Any]:
    raw_metadata = mapping_value(result, ("metadata",), {})

    if isinstance(raw_metadata, dict):
        return dict(raw_metadata)

    return {}


def _first_value(
    result: Any,
    metadata: dict[str, Any],
    names: tuple[str, ...],
    default: Any = None,
) -> Any:
    value = mapping_value(result, names, None)

    if value is not None:
        return value

    for name in names:
        if name in metadata:
            return metadata[name]

    return default


def _normalize_chunk_index(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_candidate(result: Any) -> RankingCandidate:
    """Convert a retrieval result into a ranking candidate."""

    metadata = _extract_metadata(result)

    text = str(_first_value(result, metadata, _TEXT_FIELDS, "") or "")
    source = str(_first_value(result, metadata, _SOURCE_FIELDS, "") or "")

    if source:
        source = str(Path(source).expanduser())

    chunk_index = _normalize_chunk_index(
        _first_value(result, metadata, _CHUNK_FIELDS)
    )

    raw_score = _first_value(result, metadata, _SCORE_FIELDS, 0.0)
    raw_quality = _first_value(result, metadata, _QUALITY_FIELDS, 0.0)

    created_at = _first_value(result, metadata, _CREATED_FIELDS)
    updated_at = _first_value(result, metadata, _UPDATED_FIELDS)

    return RankingCandidate(
        original=result,
        text=text,
        source=source,
        chunk_index=chunk_index,
        semantic_score=normalize_semantic_score(raw_score),
        quality_score=normalize_quality_score(raw_quality),
        created_at=str(created_at) if created_at is not None else None,
        updated_at=str(updated_at) if updated_at is not None else None,
        metadata=metadata,
    )


def normalize_candidates(results: Iterable[Any]) -> list[RankingCandidate]:
    return [normalize_candidate(result) for result in results]
