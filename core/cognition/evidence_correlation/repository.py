"""Repository for Genesis IV-A4 hypothesis assessments."""

from __future__ import annotations

from threading import RLock
from typing import Sequence

from .errors import (
    AssessmentNotFoundError,
    AssessmentRepositoryClosedError,
)
from .models import AssessmentQuery, HypothesisAssessment


class InMemoryAssessmentRepository:
    """Thread-safe deterministic in-memory assessment repository."""

    def __init__(self) -> None:
        self._records: dict[str, HypothesisAssessment] = {}
        self._order: list[str] = []
        self._closed = False
        self._lock = RLock()

    def _require_open(self) -> None:
        if self._closed:
            raise AssessmentRepositoryClosedError(
                "assessment repository is closed"
            )

    def put(self, assessment: HypothesisAssessment) -> bool:
        """Insert an assessment idempotently."""

        if not isinstance(assessment, HypothesisAssessment):
            raise TypeError("assessment must be HypothesisAssessment")

        with self._lock:
            self._require_open()
            if assessment.assessment_id in self._records:
                return False
            self._records[assessment.assessment_id] = assessment
            self._order.append(assessment.assessment_id)
            return True

    def get(self, assessment_id: str) -> HypothesisAssessment:
        """Return one assessment."""

        with self._lock:
            self._require_open()
            try:
                return self._records[assessment_id]
            except KeyError as exc:
                raise AssessmentNotFoundError(
                    f"assessment not found: {assessment_id}"
                ) from exc

    def query(
        self,
        query: AssessmentQuery,
    ) -> Sequence[HypothesisAssessment]:
        """Return assessments matching the supplied query."""

        if not isinstance(query, AssessmentQuery):
            raise TypeError("query must be AssessmentQuery")

        with self._lock:
            self._require_open()
            values = [self._records[item] for item in self._order]

        filtered: list[HypothesisAssessment] = []
        for assessment in values:
            if (
                query.situation_id is not None
                and assessment.situation_id != query.situation_id
            ):
                continue
            if (
                query.hypothesis_id is not None
                and assessment.hypothesis_id != query.hypothesis_id
            ):
                continue
            if (
                query.status is not None
                and assessment.status is not query.status
            ):
                continue
            if (
                query.minimum_confidence is not None
                and assessment.confidence < query.minimum_confidence
            ):
                continue
            if (
                query.minimum_coverage is not None
                and assessment.coverage < query.minimum_coverage
            ):
                continue
            filtered.append(assessment)

        filtered.sort(
            key=lambda item: (
                item.net_score,
                item.confidence,
                item.assessment_id,
            ),
            reverse=query.strongest_first,
        )

        if query.limit is not None:
            filtered = filtered[: query.limit]

        return tuple(filtered)

    def count(self) -> int:
        """Return repository size."""

        with self._lock:
            self._require_open()
            return len(self._records)

    def close(self) -> None:
        """Close the repository."""

        with self._lock:
            self._closed = True
