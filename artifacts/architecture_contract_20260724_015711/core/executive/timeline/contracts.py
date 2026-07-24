"""Immutable contracts for Genesis VI-A6.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

GENESIS_FINGERPRINT = "0" * 64

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

def fingerprint(value: object) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()

class TimelineError(RuntimeError):
    pass

class InvalidTimelineEventError(TimelineError):
    pass

class TimelineSubsystem(str, Enum):
    EXECUTIVE = "executive"
    LIFECYCLE = "lifecycle"
    MISSION = "mission"
    OBSERVATION = "observation"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    DECISION = "decision"
    PERSISTENCE = "persistence"
    INTEGRITY = "integrity"
    RECOVERY = "recovery"
    OPERATOR = "operator"
    SYSTEM = "system"

class TimelineEventKind(str, Enum):
    EXECUTIVE_BOOT_STARTED = "executive_boot_started"
    EXECUTIVE_BOOT_COMPLETED = "executive_boot_completed"
    EXECUTIVE_SHUTDOWN_STARTED = "executive_shutdown_started"
    EXECUTIVE_SHUTDOWN_COMPLETED = "executive_shutdown_completed"
    EXECUTIVE_FAILURE = "executive_failure"
    SESSION_CREATED = "session_created"
    SESSION_ACTIVATED = "session_activated"
    SESSION_SUSPENDED = "session_suspended"
    SESSION_RESUMED = "session_resumed"
    SESSION_COMPLETED = "session_completed"
    SESSION_ABORTED = "session_aborted"
    MISSION_CREATED = "mission_created"
    MISSION_STARTED = "mission_started"
    MISSION_COMPLETED = "mission_completed"
    MISSION_ABORTED = "mission_aborted"
    OBJECTIVE_STARTED = "objective_started"
    OBJECTIVE_COMPLETED = "objective_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    ACTIVITY_STARTED = "activity_started"
    ACTIVITY_COMPLETED = "activity_completed"
    OBSERVATION_RECEIVED = "observation_received"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    REASONING_STARTED = "reasoning_started"
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    HYPOTHESIS_SELECTED = "hypothesis_selected"
    DECISION_PROPOSED = "decision_proposed"
    DECISION_CERTIFIED = "decision_certified"
    CHECKPOINT_STARTED = "checkpoint_started"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_VERIFIED = "checkpoint_verified"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_REFUSED = "recovery_refused"
    OPERATOR_COMMAND = "operator_command"
    NOTE_RECORDED = "note_recorded"

@dataclass(frozen=True, slots=True)
class TimelineContext:
    session_id: str | None = None
    mission_id: str | None = None
    objective_id: str | None = None
    task_id: str | None = None
    activity_id: str | None = None
    correlation_id: str | None = None

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "session_id": self.session_id, "mission_id": self.mission_id,
            "objective_id": self.objective_id, "task_id": self.task_id,
            "activity_id": self.activity_id, "correlation_id": self.correlation_id,
        }

@dataclass(frozen=True, slots=True)
class TimelineEventDraft:
    subsystem: TimelineSubsystem
    kind: TimelineEventKind
    context: TimelineContext = field(default_factory=TimelineContext)
    payload: Mapping[str, object] = field(default_factory=dict)
    parent_event_id: str | None = None
    occurred_at: datetime | None = None

    def validate(self) -> None:
        if not isinstance(self.subsystem, TimelineSubsystem):
            raise InvalidTimelineEventError("Invalid subsystem.")
        if not isinstance(self.kind, TimelineEventKind):
            raise InvalidTimelineEventError("Invalid event kind.")
        if not isinstance(self.context, TimelineContext):
            raise InvalidTimelineEventError("Invalid context.")
        if not isinstance(self.payload, Mapping):
            raise InvalidTimelineEventError("Payload must be a mapping.")
        if self.occurred_at is not None and self.occurred_at.tzinfo is None:
            raise InvalidTimelineEventError("occurred_at must be timezone-aware.")

@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: str
    sequence: int
    occurred_at: datetime
    subsystem: TimelineSubsystem
    kind: TimelineEventKind
    context: TimelineContext
    payload: Mapping[str, object]
    parent_event_id: str | None
    previous_event_fingerprint: str
    event_fingerprint: str

    @classmethod
    def create(cls, *, event_id: str, sequence: int, occurred_at: datetime,
               subsystem: TimelineSubsystem, kind: TimelineEventKind,
               context: TimelineContext, payload: Mapping[str, object],
               parent_event_id: str | None,
               previous_event_fingerprint: str) -> "TimelineEvent":
        material = {
            "event_id": event_id, "sequence": sequence,
            "occurred_at": occurred_at.isoformat(), "subsystem": subsystem.value,
            "kind": kind.value, "context": context.canonical_dict(),
            "payload": dict(payload), "parent_event_id": parent_event_id,
            "previous_event_fingerprint": previous_event_fingerprint,
        }
        return cls(event_id, sequence, occurred_at, subsystem, kind, context,
                   dict(payload), parent_event_id, previous_event_fingerprint,
                   fingerprint(material))

    def material(self) -> dict[str, object]:
        return {
            "event_id": self.event_id, "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "subsystem": self.subsystem.value, "kind": self.kind.value,
            "context": self.context.canonical_dict(), "payload": dict(self.payload),
            "parent_event_id": self.parent_event_id,
            "previous_event_fingerprint": self.previous_event_fingerprint,
        }

    def verify_fingerprint(self) -> bool:
        return fingerprint(self.material()) == self.event_fingerprint

@dataclass(frozen=True, slots=True)
class TimelineIntegrityReport:
    certified: bool
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    terminal_fingerprint: str
    findings: tuple[str, ...]
    report_fingerprint: str

    @classmethod
    def create(cls, events: Sequence[TimelineEvent], findings: Iterable[str]) -> "TimelineIntegrityReport":
        f = tuple(findings)
        material = {
            "certified": not f, "event_count": len(events),
            "first_sequence": events[0].sequence if events else None,
            "last_sequence": events[-1].sequence if events else None,
            "terminal_fingerprint": events[-1].event_fingerprint if events else GENESIS_FINGERPRINT,
            "findings": f,
        }
        return cls(not f, len(events), material["first_sequence"],
                   material["last_sequence"], material["terminal_fingerprint"],
                   f, fingerprint(material))
