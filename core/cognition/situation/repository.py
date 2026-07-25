"""Repository implementation for Genesis IV-A2 situations."""

from __future__ import annotations

from threading import RLock
from typing import Sequence

from core.cognition.observation import ObservationSeverity

from .errors import (
    SituationNotFoundError,
    SituationRepositoryClosedError,
)
from .models import SituationQuery, SituationSnapshot


_SEVERITY_RANK = {
    ObservationSeverity.DEBUG: 0,
    ObservationSeverity.INFORMATIONAL: 1,
    ObservationSeverity.NOTICE: 2,
    ObservationSeverity.WARNING: 3,
    ObservationSeverity.ERROR: 4,
    ObservationSeverity.CRITICAL: 5,
}


class InMemorySituationRepository:
    """Thread-safe deterministic in-memory situation repository."""

    def __init__(self) -> None:
        self._records: dict[str, SituationSnapshot] = {}
        self._order: list[str] = []
        self._closed = False
        self._lock = RLock()

    def _require_open(self) -> None:
        if self._closed:
            raise SituationRepositoryClosedError(
                "situation repository is closed"
            )

    def put(self, situation: SituationSnapshot) -> bool:
        """Insert a situation idempotently."""

        if not isinstance(situation, SituationSnapshot):
            raise TypeError("situation must be SituationSnapshot")

        with self._lock:
            self._require_open()
            if situation.situation_id in self._records:
                return False
            self._records[situation.situation_id] = situation
            self._order.append(situation.situation_id)
            return True

    def get(self, situation_id: str) -> SituationSnapshot:
        """Return one situation."""

        with self._lock:
            self._require_open()
            try:
                return self._records[situation_id]
            except KeyError as exc:
                raise SituationNotFoundError(
                    f"situation not found: {situation_id}"
                ) from exc

    def query(self, query: SituationQuery) -> Sequence[SituationSnapshot]:
        """Return situations matching the supplied query."""

        if not isinstance(query, SituationQuery):
            raise TypeError("query must be SituationQuery")

        with self._lock:
            self._require_open()
            values = [self._records[item] for item in self._order]

        filtered: list[SituationSnapshot] = []

        for situation in values:
            if query.status is not None and situation.status is not query.status:
                continue
            if (
                query.mission_id is not None
                and situation.mission_id != query.mission_id
            ):
                continue
            if (
                query.correlation_id is not None
                and situation.correlation_id != query.correlation_id
            ):
                continue
            if (
                query.minimum_confidence is not None
                and situation.confidence < query.minimum_confidence
            ):
                continue
            if query.minimum_severity is not None:
                if (
                    _SEVERITY_RANK[situation.severity]
                    < _SEVERITY_RANK[query.minimum_severity]
                ):
                    continue
            if (
                query.updated_from is not None
                and situation.updated_at < query.updated_from
            ):
                continue
            if (
                query.updated_to is not None
                and situation.updated_at > query.updated_to
            ):
                continue
            filtered.append(situation)

        filtered.sort(
            key=lambda item: (item.updated_at, item.situation_id),
            reverse=query.newest_first,
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
