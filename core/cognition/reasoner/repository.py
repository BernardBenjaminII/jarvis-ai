"""Repository for Genesis IV-A5 reasoning results."""

from __future__ import annotations

from threading import RLock
from typing import Sequence

from .errors import (
    ReasoningRepositoryClosedError,
    ReasoningResultNotFoundError,
)
from .models import ExecutiveReasoningResult, ReasoningQuery


class InMemoryReasoningRepository:
    """Thread-safe deterministic in-memory reasoning repository."""

    def __init__(self) -> None:
        self._records: dict[str, ExecutiveReasoningResult] = {}
        self._order: list[str] = []
        self._closed = False
        self._lock = RLock()

    def _require_open(self) -> None:
        if self._closed:
            raise ReasoningRepositoryClosedError(
                "reasoning repository is closed"
            )

    def put(self, result: ExecutiveReasoningResult) -> bool:
        if not isinstance(result, ExecutiveReasoningResult):
            raise TypeError("result must be ExecutiveReasoningResult")
        with self._lock:
            self._require_open()
            if result.reasoning_id in self._records:
                return False
            self._records[result.reasoning_id] = result
            self._order.append(result.reasoning_id)
            return True

    def get(self, reasoning_id: str) -> ExecutiveReasoningResult:
        with self._lock:
            self._require_open()
            try:
                return self._records[reasoning_id]
            except KeyError as exc:
                raise ReasoningResultNotFoundError(
                    f"reasoning result not found: {reasoning_id}"
                ) from exc

    def query(
        self,
        query: ReasoningQuery,
    ) -> Sequence[ExecutiveReasoningResult]:
        if not isinstance(query, ReasoningQuery):
            raise TypeError("query must be ReasoningQuery")

        with self._lock:
            self._require_open()
            values = [self._records[item] for item in self._order]

        filtered: list[ExecutiveReasoningResult] = []
        for result in values:
            if (
                query.situation_id is not None
                and result.situation_id != query.situation_id
            ):
                continue
            if (
                query.disposition is not None
                and result.disposition is not query.disposition
            ):
                continue
            if (
                query.minimum_confidence is not None
                and result.confidence < query.minimum_confidence
            ):
                continue
            filtered.append(result)

        filtered.sort(
            key=lambda item: (
                item.confidence,
                item.margin,
                item.reasoning_id,
            ),
            reverse=query.strongest_first,
        )

        if query.limit is not None:
            filtered = filtered[: query.limit]

        return tuple(filtered)

    def count(self) -> int:
        with self._lock:
            self._require_open()
            return len(self._records)

    def close(self) -> None:
        with self._lock:
            self._closed = True
