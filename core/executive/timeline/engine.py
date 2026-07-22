"""Append-only Executive Timeline Engine."""
from __future__ import annotations
from collections.abc import Iterable
from typing import Callable
from uuid import uuid4
from .contracts import (
    GENESIS_FINGERPRINT, InvalidTimelineEventError, TimelineEvent,
    TimelineEventDraft, TimelineIntegrityReport, utc_now,
)
from .queries import TimelineQuery, execute_query

class ExecutiveTimelineEngine:
    def __init__(self, *, event_id_factory: Callable[[int], str] | None = None) -> None:
        self._events: list[TimelineEvent] = []
        self._event_id_factory = event_id_factory or (
            lambda n: f"timeline-event-{n:08d}-{uuid4().hex}"
        )

    @property
    def events(self) -> tuple[TimelineEvent, ...]:
        return tuple(self._events)

    @property
    def terminal_fingerprint(self) -> str:
        return self._events[-1].event_fingerprint if self._events else GENESIS_FINGERPRINT

    def append(self, draft: TimelineEventDraft) -> TimelineEvent:
        draft.validate()
        sequence = len(self._events) + 1
        event_id = self._event_id_factory(sequence)
        if not event_id or any(e.event_id == event_id for e in self._events):
            raise InvalidTimelineEventError("Event ID must be unique and non-empty.")
        if draft.parent_event_id is not None and not any(
            e.event_id == draft.parent_event_id for e in self._events
        ):
            raise InvalidTimelineEventError("Parent must reference an earlier event.")
        event = TimelineEvent.create(
            event_id=event_id, sequence=sequence,
            occurred_at=draft.occurred_at or utc_now(),
            subsystem=draft.subsystem, kind=draft.kind, context=draft.context,
            payload=draft.payload, parent_event_id=draft.parent_event_id,
            previous_event_fingerprint=self.terminal_fingerprint,
        )
        self._events.append(event)
        return event

    def append_many(self, drafts: Iterable[TimelineEventDraft]) -> tuple[TimelineEvent, ...]:
        return tuple(self.append(draft) for draft in drafts)

    def query(self, query: TimelineQuery) -> tuple[TimelineEvent, ...]:
        return execute_query(self._events, query)

    def latest(self, limit: int = 25) -> tuple[TimelineEvent, ...]:
        return self.query(TimelineQuery(limit=limit, newest_first=True))

    def verify(self) -> TimelineIntegrityReport:
        findings = []
        expected_previous = GENESIS_FINGERPRINT
        seen: set[str] = set()
        for expected_sequence, event in enumerate(self._events, 1):
            if event.sequence != expected_sequence:
                findings.append(f"Sequence mismatch at {expected_sequence}.")
            if event.event_id in seen:
                findings.append(f"Duplicate event ID: {event.event_id}.")
            if event.previous_event_fingerprint != expected_previous:
                findings.append(f"Broken chain before sequence {event.sequence}.")
            if not event.verify_fingerprint():
                findings.append(f"Invalid event fingerprint at sequence {event.sequence}.")
            if event.parent_event_id is not None and event.parent_event_id not in seen:
                findings.append(f"Invalid parent at sequence {event.sequence}.")
            seen.add(event.event_id)
            expected_previous = event.event_fingerprint
        return TimelineIntegrityReport.create(self._events, findings)
