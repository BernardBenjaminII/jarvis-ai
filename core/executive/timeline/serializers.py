"""Canonical TimelineEvent serialization for VI-A6.8 Part A."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Mapping

from .contracts import (
    TimelineContext,
    TimelineEvent,
    TimelineEventKind,
    TimelineSubsystem,
)
from .repository_contracts import (
    TIMELINE_REPOSITORY_SCHEMA,
    TIMELINE_REPOSITORY_SCHEMA_VERSION,
    TimelineRepositoryIntegrityError,
)


class TimelineEventSerializer:
    """Stable JSON codec for immutable A6.7 timeline events."""

    @staticmethod
    def to_record(event: TimelineEvent) -> dict[str, object]:
        return {
            "schema": TIMELINE_REPOSITORY_SCHEMA,
            "schema_version": TIMELINE_REPOSITORY_SCHEMA_VERSION,
            "event": {
                "event_id": event.event_id,
                "sequence": event.sequence,
                "occurred_at": event.occurred_at.isoformat(),
                "subsystem": event.subsystem.value,
                "kind": event.kind.value,
                "context": event.context.canonical_dict(),
                "payload": dict(event.payload),
                "parent_event_id": event.parent_event_id,
                "previous_event_fingerprint": event.previous_event_fingerprint,
                "event_fingerprint": event.event_fingerprint,
            },
        }

    @classmethod
    def dumps(cls, event: TimelineEvent) -> str:
        return json.dumps(
            cls.to_record(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def dump_line(cls, event: TimelineEvent) -> bytes:
        return (cls.dumps(event) + "\n").encode("utf-8")

    @staticmethod
    def _context(value: object) -> TimelineContext:
        if not isinstance(value, Mapping):
            raise TimelineRepositoryIntegrityError("Event context must be an object.")
        return TimelineContext(
            session_id=value.get("session_id"),
            mission_id=value.get("mission_id"),
            objective_id=value.get("objective_id"),
            task_id=value.get("task_id"),
            activity_id=value.get("activity_id"),
            correlation_id=value.get("correlation_id"),
        )

    @classmethod
    def loads(cls, raw: str | bytes) -> TimelineEvent:
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            record = json.loads(raw)
            if record.get("schema") != TIMELINE_REPOSITORY_SCHEMA:
                raise TimelineRepositoryIntegrityError("Unknown timeline repository schema.")
            if record.get("schema_version") != TIMELINE_REPOSITORY_SCHEMA_VERSION:
                raise TimelineRepositoryIntegrityError("Unsupported timeline schema version.")
            value = record["event"]
            occurred_at = datetime.fromisoformat(value["occurred_at"])
            if occurred_at.tzinfo is None:
                raise TimelineRepositoryIntegrityError("Persisted timestamp is not timezone-aware.")
            event = TimelineEvent(
                event_id=value["event_id"],
                sequence=int(value["sequence"]),
                occurred_at=occurred_at,
                subsystem=TimelineSubsystem(value["subsystem"]),
                kind=TimelineEventKind(value["kind"]),
                context=cls._context(value["context"]),
                payload=dict(value["payload"]),
                parent_event_id=value.get("parent_event_id"),
                previous_event_fingerprint=value["previous_event_fingerprint"],
                event_fingerprint=value["event_fingerprint"],
            )
        except TimelineRepositoryIntegrityError:
            raise
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise TimelineRepositoryIntegrityError(
                f"Invalid persisted timeline record: {exc}"
            ) from exc
        if not event.verify_fingerprint():
            raise TimelineRepositoryIntegrityError(
                f"Invalid event fingerprint at sequence {event.sequence}."
            )
        return event
