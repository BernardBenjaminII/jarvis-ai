"""Repository implementation for Genesis IV-A3 hypotheses."""

from __future__ import annotations

from threading import RLock
from typing import Sequence

from .errors import (
    HypothesisNotFoundError,
    HypothesisRepositoryClosedError,
)
from .models import Hypothesis, HypothesisQuery


class InMemoryHypothesisRepository:
    """Thread-safe deterministic in-memory hypothesis repository."""

    def __init__(self) -> None:
        self._records: dict[str, Hypothesis] = {}
        self._order: list[str] = []
        self._closed = False
        self._lock = RLock()

    def _require_open(self) -> None:
        if self._closed:
            raise HypothesisRepositoryClosedError(
                "hypothesis repository is closed"
            )

    def put(self, hypothesis: Hypothesis) -> bool:
        """Insert a hypothesis idempotently."""

        if not isinstance(hypothesis, Hypothesis):
            raise TypeError("hypothesis must be Hypothesis")

        with self._lock:
            self._require_open()
            if hypothesis.hypothesis_id in self._records:
                return False
            self._records[hypothesis.hypothesis_id] = hypothesis
            self._order.append(hypothesis.hypothesis_id)
            return True

    def get(self, hypothesis_id: str) -> Hypothesis:
        """Return one hypothesis."""

        with self._lock:
            self._require_open()
            try:
                return self._records[hypothesis_id]
            except KeyError as exc:
                raise HypothesisNotFoundError(
                    f"hypothesis not found: {hypothesis_id}"
                ) from exc

    def query(self, query: HypothesisQuery) -> Sequence[Hypothesis]:
        """Return hypotheses matching the supplied query."""

        if not isinstance(query, HypothesisQuery):
            raise TypeError("query must be HypothesisQuery")

        with self._lock:
            self._require_open()
            values = [self._records[item] for item in self._order]

        filtered: list[Hypothesis] = []

        for hypothesis in values:
            if (
                query.situation_id is not None
                and hypothesis.situation_id != query.situation_id
            ):
                continue
            if query.kind is not None and hypothesis.kind is not query.kind:
                continue
            if (
                query.status is not None
                and hypothesis.status is not query.status
            ):
                continue
            if (
                query.minimum_confidence is not None
                and hypothesis.confidence < query.minimum_confidence
            ):
                continue
            filtered.append(hypothesis)

        filtered.sort(
            key=lambda item: (item.confidence, item.hypothesis_id),
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
