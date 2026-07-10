"""Filtering and confidence analysis for Retrieval Intelligence."""

from __future__ import annotations

from collections.abc import Iterable

from knowledge_engine.retrieval_intelligence.models import RetrievalCandidate


DEFAULT_MINIMUM_SIMILARITY = 0.55


class CandidateFilter:
    """Reject candidates that do not meet retrieval-confidence policy."""

    def __init__(
        self,
        *,
        minimum_similarity: float = DEFAULT_MINIMUM_SIMILARITY,
    ) -> None:
        if not 0.0 <= minimum_similarity <= 1.0:
            raise ValueError(
                "minimum_similarity must be between 0.0 and 1.0."
            )

        self.minimum_similarity = minimum_similarity

    def apply(
        self,
        candidates: Iterable[RetrievalCandidate],
    ) -> tuple[list[RetrievalCandidate], list[RetrievalCandidate]]:
        accepted: list[RetrievalCandidate] = []
        rejected: list[RetrievalCandidate] = []

        for candidate in candidates:
            if candidate.normalized_score >= self.minimum_similarity:
                accepted.append(candidate)
            else:
                rejected.append(candidate)

        return accepted, rejected


def confidence_label(
    candidates: list[RetrievalCandidate],
) -> str:
    """Classify retrieval confidence from accepted candidate scores."""

    if not candidates:
        return "none"

    top_score = candidates[0].normalized_score

    top_three = candidates[:3]

    average = sum(
        item.normalized_score
        for item in top_three
    ) / len(top_three)

    if top_score >= 0.82 and average >= 0.72:
        return "high"

    if top_score >= 0.68 and average >= 0.60:
        return "medium"

    return "low"
