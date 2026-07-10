"""Candidate normalization for Retrieval Intelligence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from knowledge_engine.retrieval_intelligence.models import RetrievalCandidate


def normalize_similarity(value: Any) -> float:
    """Normalize cosine similarity or percentage similarity to 0.0–1.0.

    Supported forms:

    - cosine values from -1.0 through 1.0;
    - already-normalized values from 0.0 through 1.0;
    - percentages from 0 through 100.

    Negative cosine values are translated using:

        normalized = (score + 1) / 2
    """

    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    if score > 1.0:
        if score <= 100.0:
            return max(0.0, min(1.0, score / 100.0))

        return 1.0

    if score < 0.0:
        return max(0.0, min(1.0, (score + 1.0) / 2.0))

    return max(0.0, min(1.0, score))


def _integer_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_candidate(
    value: Any,
    *,
    provider: str,
) -> RetrievalCandidate:
    """Normalize a tuple, mapping, or attribute object.

    Production vector retrieval currently returns:

        score, file_path, chunk_index, text
    """

    if isinstance(value, Mapping):
        raw_score = value.get(
            "raw_score",
            value.get(
                "semantic_score",
                value.get("score", 0.0),
            ),
        )

        source = value.get(
            "source",
            value.get(
                "file_path",
                value.get("path", ""),
            ),
        )

        chunk_index = value.get(
            "chunk_index",
            value.get("chunk_number", 0),
        )

        text = value.get(
            "text",
            value.get("content", ""),
        )

        metadata = value.get("metadata", {})

        if not isinstance(metadata, Mapping):
            metadata = {}

        return RetrievalCandidate(
            text=str(text or ""),
            source=str(source or ""),
            chunk_index=_integer_value(chunk_index),
            raw_score=_float_value(raw_score),
            normalized_score=normalize_similarity(raw_score),
            provider=provider,
            metadata=dict(metadata),
        )

    if isinstance(value, (tuple, list)):
        if len(value) != 4:
            raise ValueError(
                "Tuple retrieval results must contain exactly four values: "
                "(score, file_path, chunk_index, text)."
            )

        raw_score, source, chunk_index, text = value

        return RetrievalCandidate(
            text=str(text or ""),
            source=str(source or ""),
            chunk_index=_integer_value(chunk_index),
            raw_score=_float_value(raw_score),
            normalized_score=normalize_similarity(raw_score),
            provider=provider,
        )

    raw_score = getattr(
        value,
        "raw_score",
        getattr(
            value,
            "semantic_score",
            getattr(value, "score", 0.0),
        ),
    )

    source = getattr(
        value,
        "source",
        getattr(
            value,
            "file_path",
            getattr(value, "path", ""),
        ),
    )

    chunk_index = getattr(
        value,
        "chunk_index",
        getattr(value, "chunk_number", 0),
    )

    text = getattr(
        value,
        "text",
        getattr(value, "content", ""),
    )

    return RetrievalCandidate(
        text=str(text or ""),
        source=str(source or ""),
        chunk_index=_integer_value(chunk_index),
        raw_score=_float_value(raw_score),
        normalized_score=normalize_similarity(raw_score),
        provider=provider,
    )
