"""Data models used by the JARVIS Knowledge Ranking Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RankingWeights:
    """Weights used to calculate a candidate's final ranking score."""

    semantic: float = 0.42
    lexical: float = 0.20
    quality: float = 0.12
    authority: float = 0.10
    completeness: float = 0.08
    freshness: float = 0.04
    diversity: float = 0.04

    def __post_init__(self) -> None:
        values = (
            self.semantic,
            self.lexical,
            self.quality,
            self.authority,
            self.completeness,
            self.freshness,
            self.diversity,
        )

        if any(value < 0.0 for value in values):
            raise ValueError("Ranking weights cannot be negative.")

        total = sum(values)

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"Ranking weights must total 1.0; received {total:.6f}."
            )


@dataclass(frozen=True, slots=True)
class RankingBreakdown:
    """Explainable component scores for a ranked candidate."""

    semantic: float
    lexical: float
    quality: float
    authority: float
    completeness: float
    freshness: float
    diversity: float
    duplicate_penalty: float
    final_score: float

    def as_dict(self) -> dict[str, float]:
        return {
            "semantic": round(self.semantic, 6),
            "lexical": round(self.lexical, 6),
            "quality": round(self.quality, 6),
            "authority": round(self.authority, 6),
            "completeness": round(self.completeness, 6),
            "freshness": round(self.freshness, 6),
            "diversity": round(self.diversity, 6),
            "duplicate_penalty": round(self.duplicate_penalty, 6),
            "final_score": round(self.final_score, 6),
        }


@dataclass(slots=True)
class RankingCandidate:
    """Normalized representation of a retrieval result."""

    original: Any
    text: str
    source: str
    chunk_index: int | None
    semantic_score: float
    quality_score: float
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    breakdown: RankingBreakdown | None = None

    def identity(self) -> tuple[str, int | None]:
        return self.source, self.chunk_index


def mapping_value(
    value: Any,
    names: tuple[str, ...],
    default: Any = None,
) -> Any:
    """Read a value from either a mapping or an attribute-based object."""

    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default

    for name in names:
        if hasattr(value, name):
            return getattr(value, name)

    return default
