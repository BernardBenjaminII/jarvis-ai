"""Models used by the JARVIS Retrieval Intelligence pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalCandidate:
    """Canonical candidate shared by all retrieval providers."""

    text: str
    source: str
    chunk_index: int
    raw_score: float
    normalized_score: float
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def identity(self) -> tuple[str, int]:
        """Return the stable identity used for candidate merging."""

        return self.source, self.chunk_index

    def as_mapping(self) -> dict[str, Any]:
        """Return a ranking-compatible mapping."""

        return {
            "text": self.text,
            "content": self.text,
            "source": self.source,
            "file_path": self.source,
            "chunk_index": self.chunk_index,

            # Preserve the underlying retrieval score for compatibility with
            # the existing ranking normalization logic.
            "score": self.raw_score,

            "retrieval_score_normalized": self.normalized_score,
            "retrieval_provider": self.provider,
            "retrieval_metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProviderDiagnostics:
    """Diagnostics reported by one retrieval provider."""

    provider: str
    returned: int
    accepted: int
    rejected: int
    highest_score: float
    average_score: float


@dataclass(frozen=True, slots=True)
class RetrievalDiagnostics:
    """Summary of one complete intelligent-retrieval operation."""

    query: str
    requested_limit: int
    provider_count: int
    retrieved_candidates: int
    merged_candidates: int
    accepted_candidates: int
    rejected_candidates: int
    minimum_similarity: float
    highest_similarity: float
    average_similarity: float
    confidence: str
    providers: tuple[ProviderDiagnostics, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a stable serializable representation."""

        return {
            "query": self.query,
            "requested_limit": self.requested_limit,
            "provider_count": self.provider_count,
            "retrieved_candidates": self.retrieved_candidates,
            "merged_candidates": self.merged_candidates,
            "accepted_candidates": self.accepted_candidates,
            "rejected_candidates": self.rejected_candidates,
            "minimum_similarity": round(self.minimum_similarity, 6),
            "highest_similarity": round(self.highest_similarity, 6),
            "average_similarity": round(self.average_similarity, 6),
            "confidence": self.confidence,
            "providers": [
                {
                    "provider": item.provider,
                    "returned": item.returned,
                    "accepted": item.accepted,
                    "rejected": item.rejected,
                    "highest_score": round(item.highest_score, 6),
                    "average_score": round(item.average_score, 6),
                }
                for item in self.providers
            ],
        }
