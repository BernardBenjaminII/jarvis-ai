"""Certified append-only Executive Timeline Repository foundation."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from threading import RLock

from .contracts import GENESIS_FINGERPRINT, TimelineEvent
from .indexes import TimelineRepositoryIndexes
from .repository_contracts import (
    TimelineRepositoryConflictError,
    TimelineRepositoryIntegrityError,
    TimelineRepositoryIntegrityReport,
    TimelineRepositoryStatistics,
)
from .serializers import TimelineEventSerializer
from .storage import AppendOnlyTimelineStorage


class ExecutiveTimelineRepository:
    """Persistent authority for already-created VI-A6.7 TimelineEvent objects."""

    def __init__(self, root: str | Path) -> None:
        self._storage = AppendOnlyTimelineStorage(root)
        self._lock = RLock()
        self._events: tuple[TimelineEvent, ...] = ()
        self._indexes = TimelineRepositoryIndexes.build(())
        self.reload()

    @property
    def storage_path(self) -> Path:
        return self._storage.path

    @property
    def events(self) -> tuple[TimelineEvent, ...]:
        return self._events

    @property
    def indexes(self) -> TimelineRepositoryIndexes:
        return self._indexes

    @property
    def terminal_fingerprint(self) -> str:
        return self._events[-1].event_fingerprint if self._events else GENESIS_FINGERPRINT

    def _certify_candidate(self, events: tuple[TimelineEvent, ...]) -> None:
        findings: list[str] = []
        previous = GENESIS_FINGERPRINT
        seen: set[str] = set()
        for expected, event in enumerate(events, 1):
            if event.sequence != expected:
                findings.append(
                    f"Sequence mismatch: expected {expected}, found {event.sequence}."
                )
            if event.event_id in seen:
                findings.append(f"Duplicate event ID: {event.event_id}.")
            if event.previous_event_fingerprint != previous:
                findings.append(f"Broken chain before sequence {event.sequence}.")
            if not event.verify_fingerprint():
                findings.append(f"Invalid fingerprint at sequence {event.sequence}.")
            if event.parent_event_id is not None and event.parent_event_id not in seen:
                findings.append(f"Invalid parent at sequence {event.sequence}.")
            seen.add(event.event_id)
            previous = event.event_fingerprint
        if findings:
            raise TimelineRepositoryIntegrityError("; ".join(findings))

    def reload(self) -> tuple[TimelineEvent, ...]:
        with self._lock:
            events = tuple(
                TimelineEventSerializer.loads(line)
                for line in self._storage.iter_lines()
            )
            self._certify_candidate(events)
            self._events = events
            self._indexes = TimelineRepositoryIndexes.build(events)
            return events

    def append(self, event: TimelineEvent) -> TimelineEvent:
        return self.append_many((event,))[0]

    def append_many(self, events: Iterable[TimelineEvent]) -> tuple[TimelineEvent, ...]:
        incoming = tuple(events)
        if not incoming:
            return ()
        with self._lock:
            candidate = self._events + incoming
            try:
                self._certify_candidate(candidate)
            except TimelineRepositoryIntegrityError as exc:
                raise TimelineRepositoryConflictError(str(exc)) from exc
            self._storage.append_many(
                TimelineEventSerializer.dump_line(event) for event in incoming
            )
            self._events = candidate
            self._indexes = TimelineRepositoryIndexes.build(candidate)
            return incoming

    def get(self, event_id: str) -> TimelineEvent | None:
        sequence = self._indexes.by_event_id.get(event_id)
        return self._events[sequence - 1] if sequence is not None else None

    def load_session(self, session_id: str) -> tuple[TimelineEvent, ...]:
        return self._select(self._indexes.by_session.get(session_id, ()))

    def load_mission(self, mission_id: str) -> tuple[TimelineEvent, ...]:
        return self._select(self._indexes.by_mission.get(mission_id, ()))

    def _select(self, sequences: Iterable[int]) -> tuple[TimelineEvent, ...]:
        return tuple(self._events[sequence - 1] for sequence in sequences)

    def latest(self, limit: int = 25) -> tuple[TimelineEvent, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative.")
        if limit == 0:
            return ()
        return tuple(reversed(self._events[-limit:]))

    def statistics(self) -> TimelineRepositoryStatistics:
        return TimelineRepositoryStatistics.create(
            event_count=len(self._events),
            session_count=len(self._indexes.by_session),
            mission_count=len(self._indexes.by_mission),
            subsystem_count=len(self._indexes.by_subsystem),
            first_sequence=self._events[0].sequence if self._events else None,
            last_sequence=self._events[-1].sequence if self._events else None,
            terminal_fingerprint=self.terminal_fingerprint,
            storage_bytes=self._storage.size_bytes,
        )

    def verify(self) -> TimelineRepositoryIntegrityReport:
        findings: list[str] = []
        try:
            disk_events = tuple(
                TimelineEventSerializer.loads(line)
                for line in self._storage.iter_lines()
            )
            self._certify_candidate(disk_events)
            rebuilt = TimelineRepositoryIndexes.build(disk_events)
            if disk_events != self._events:
                findings.append("In-memory repository state differs from persisted state.")
            if rebuilt != self._indexes:
                findings.append("Repository indexes differ from deterministic rebuild.")
        except (TimelineRepositoryIntegrityError, Exception) as exc:
            findings.append(str(exc))
            disk_events = ()
        return TimelineRepositoryIntegrityReport.create(
            event_count=len(disk_events),
            first_sequence=disk_events[0].sequence if disk_events else None,
            last_sequence=disk_events[-1].sequence if disk_events else None,
            terminal_fingerprint=(
                disk_events[-1].event_fingerprint
                if disk_events
                else GENESIS_FINGERPRINT
            ),
            findings=findings,
        )
