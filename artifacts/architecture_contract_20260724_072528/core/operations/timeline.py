"""Operational timeline adapter."""

from __future__ import annotations

from datetime import datetime

from .models import TimelineEntrySnapshot, TimelineSnapshot, utc_now
from .registry import OperationsEventRegistry


class TimelineAdapter:
    """Projects canonical events into an operational timeline."""

    def __init__(self, registry: OperationsEventRegistry) -> None:
        self._registry = registry

    def collect(
        self,
        *,
        generated_at: datetime | None = None,
        limit: int = 100,
    ) -> TimelineSnapshot:
        now = generated_at or utc_now()
        entries = tuple(
            TimelineEntrySnapshot(
                event_id=event.event_id,
                event_kind=event.kind.value,
                occurred_at=event.occurred_at,
                summary=event.summary,
                subject_id=event.subject_id,
                payload=event.payload,
                provenance=event.provenance,
            )
            for event in self._registry.list_events(limit=limit)
        )
        return TimelineSnapshot(entries=entries, generated_at=now)
