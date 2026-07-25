from __future__ import annotations

from threading import RLock
from .errors import DecisionNotFoundError, DecisionRepositoryClosedError
from .models import DecisionQuery, DecisionRecord

class InMemoryDecisionRepository:
    def __init__(self) -> None:
        self._records: dict[str, DecisionRecord] = {}
        self._closed = False
        self._lock = RLock()

    def _open(self) -> None:
        if self._closed:
            raise DecisionRepositoryClosedError("decision repository is closed")

    def put(self, decision: DecisionRecord) -> bool:
        with self._lock:
            self._open()
            if decision.decision_id in self._records:
                return False
            self._records[decision.decision_id] = decision
            return True

    def get(self, decision_id: str) -> DecisionRecord:
        with self._lock:
            self._open()
            try:
                return self._records[decision_id]
            except KeyError as exc:
                raise DecisionNotFoundError(decision_id) from exc

    def query(self, query: DecisionQuery):
        with self._lock:
            self._open()
            values = list(self._records.values())
        out = []
        for item in values:
            if query.situation_id and item.situation_id != query.situation_id:
                continue
            if query.disposition and item.disposition is not query.disposition:
                continue
            if query.minimum_confidence is not None and item.confidence < query.minimum_confidence:
                continue
            out.append(item)
        out.sort(key=lambda x: x.decision_id)
        return tuple(out[:query.limit] if query.limit else out)

    def count(self) -> int:
        with self._lock:
            self._open()
            return len(self._records)

    def close(self) -> None:
        with self._lock:
            self._closed = True
