"""Thread-safe in-memory registry for Sprint 0 Operations events."""

from __future__ import annotations

from threading import RLock

from .events import OperationsEvent


class OperationsEventRegistry:
    """Stores canonical events in insertion order."""

    def __init__(self) -> None:
        self._events: list[OperationsEvent] = []
        self._lock = RLock()

    def append(self, event: OperationsEvent) -> None:
        with self._lock:
            self._events.append(event)

    def list_events(self, *, limit: int | None = None) -> tuple[OperationsEvent, ...]:
        with self._lock:
            events = tuple(self._events)
        if limit is None:
            return events
        if limit < 0:
            raise ValueError("limit must be zero or greater")
        return events[-limit:] if limit else ()

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
