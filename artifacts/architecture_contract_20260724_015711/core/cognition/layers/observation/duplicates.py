from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .models import ObservationRecord


@dataclass(frozen=True, slots=True)
class DuplicateReport:
    duplicate: bool
    similarity: float
    exact: bool
    rationale: str


class ObservationDuplicateDetector:
    def __init__(self, threshold: float = 0.96) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be within [0.0, 1.0]")
        self._threshold = threshold

    def compare(
        self,
        first: ObservationRecord,
        second: ObservationRecord,
    ) -> DuplicateReport:
        exact = first.normalized_content == second.normalized_content
        similarity = (
            1.0
            if exact
            else SequenceMatcher(
                None,
                first.normalized_content.casefold(),
                second.normalized_content.casefold(),
            ).ratio()
        )
        duplicate = exact or similarity >= self._threshold
        rationale = (
            "normalized content is identical"
            if exact
            else f"text similarity is {similarity:.4f}"
        )
        return DuplicateReport(
            duplicate=duplicate,
            similarity=similarity,
            exact=exact,
            rationale=rationale,
        )


__all__ = ("DuplicateReport", "ObservationDuplicateDetector")
