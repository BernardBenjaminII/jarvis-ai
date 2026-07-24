from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable
from uuid import UUID

from core.cognition.common.object_model import ProvenanceReference

from .duplicates import ObservationDuplicateDetector
from .errors import ObservationConflictError
from .models import ObservationRecord, utc_now


@dataclass(frozen=True, slots=True)
class MergeResult:
    """Result produced by merging two duplicate observations."""

    merged: ObservationRecord
    source_ids: tuple[UUID, UUID]
    rationale: str


class ObservationMergeEngine:
    """Merge observations that have been classified as duplicates."""

    def __init__(
        self,
        duplicate_detector: ObservationDuplicateDetector | None = None,
    ) -> None:
        self._duplicate_detector = (
            duplicate_detector or ObservationDuplicateDetector()
        )

    def merge(
        self,
        first: ObservationRecord,
        second: ObservationRecord,
    ) -> MergeResult:
        report = self._duplicate_detector.compare(first, second)

        if not report.duplicate:
            raise ObservationConflictError(
                "Observations are not sufficiently similar to merge."
            )

        preferred = (
            first
            if first.confidence >= second.confidence
            else second
        )

        combined_provenance = (*first.provenance, *second.provenance)

        combined_attributes = {
            **dict(first.attributes),
            **dict(second.attributes),
            "merged_from": sorted(
                (
                    str(first.observation_id),
                    str(second.observation_id),
                )
            ),
        }

        merged = replace(
            preferred,
            provenance=combined_provenance,
            confidence=max(first.confidence, second.confidence),
            created_at=utc_now(),
            attributes=combined_attributes,
        )

        return MergeResult(
            merged=merged,
            source_ids=(
                first.observation_id,
                second.observation_id,
            ),
            rationale=report.rationale,
        )


__all__ = (
    "MergeResult",
    "ObservationMergeEngine",
)
