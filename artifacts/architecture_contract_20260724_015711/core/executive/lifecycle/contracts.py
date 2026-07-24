"""Genesis VI-A6.6 Executive lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def fingerprint(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


class LifecycleError(RuntimeError):
    """Base class for Executive lifecycle failures."""


class InvalidLifecycleTransitionError(LifecycleError):
    """Raised when a requested state transition is not permitted."""


class SessionAlreadyActiveError(LifecycleError):
    """Raised when an operation requires no active session."""


class SessionNotActiveError(LifecycleError):
    """Raised when an operation requires an active session."""


class ExecutiveLifecycleState(str, Enum):
    OFFLINE = "offline"
    BOOTING = "booting"
    READY = "ready"
    ACTIVE = "active"
    CHECKPOINTING = "checkpointing"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"
    SHUTTING_DOWN = "shutting_down"
    FAILED = "failed"


class ExecutiveSessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    CHECKPOINTED = "checkpointed"
    SUSPENDED = "suspended"
    RECOVERED = "recovered"
    COMPLETED = "completed"
    ABORTED = "aborted"


class LifecycleEventKind(str, Enum):
    BOOT_STARTED = "boot_started"
    BOOT_COMPLETED = "boot_completed"
    SESSION_CREATED = "session_created"
    SESSION_ACTIVATED = "session_activated"
    CHECKPOINT_STARTED = "checkpoint_started"
    CHECKPOINT_COMPLETED = "checkpoint_completed"
    SESSION_SUSPENDED = "session_suspended"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    SESSION_COMPLETED = "session_completed"
    SESSION_ABORTED = "session_aborted"
    SHUTDOWN_STARTED = "shutdown_started"
    SHUTDOWN_COMPLETED = "shutdown_completed"
    FAILURE_RECORDED = "failure_recorded"


@dataclass(frozen=True, slots=True)
class ExecutiveSession:
    session_id: str
    mission_id: str
    mission_title: str
    status: ExecutiveSessionStatus
    created_at: datetime
    updated_at: datetime
    checkpoint_sequence: int = 0
    last_checkpoint_id: str | None = None
    state_fingerprint: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evolve(
        self,
        *,
        status: ExecutiveSessionStatus | None = None,
        checkpoint_sequence: int | None = None,
        last_checkpoint_id: str | None = None,
        state_fingerprint: str | None = None,
        updated_at: datetime | None = None,
    ) -> "ExecutiveSession":
        return ExecutiveSession(
            session_id=self.session_id,
            mission_id=self.mission_id,
            mission_title=self.mission_title,
            status=status or self.status,
            created_at=self.created_at,
            updated_at=updated_at or utc_now(),
            checkpoint_sequence=(
                self.checkpoint_sequence
                if checkpoint_sequence is None
                else checkpoint_sequence
            ),
            last_checkpoint_id=(
                self.last_checkpoint_id
                if last_checkpoint_id is None
                else last_checkpoint_id
            ),
            state_fingerprint=(
                self.state_fingerprint
                if state_fingerprint is None
                else state_fingerprint
            ),
            metadata=dict(self.metadata),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "mission_id": self.mission_id,
            "mission_title": self.mission_title,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checkpoint_sequence": self.checkpoint_sequence,
            "last_checkpoint_id": self.last_checkpoint_id,
            "state_fingerprint": self.state_fingerprint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    sequence: int
    kind: LifecycleEventKind
    lifecycle_state: ExecutiveLifecycleState
    session_id: str | None
    detail: str
    occurred_at: datetime
    event_fingerprint: str

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        kind: LifecycleEventKind,
        lifecycle_state: ExecutiveLifecycleState,
        session_id: str | None,
        detail: str,
        occurred_at: datetime | None = None,
    ) -> "LifecycleEvent":
        timestamp = occurred_at or utc_now()
        material = {
            "sequence": sequence,
            "kind": kind.value,
            "lifecycle_state": lifecycle_state.value,
            "session_id": session_id,
            "detail": detail,
            "occurred_at": timestamp.isoformat(),
        }
        return cls(
            sequence=sequence,
            kind=kind,
            lifecycle_state=lifecycle_state,
            session_id=session_id,
            detail=detail,
            occurred_at=timestamp,
            event_fingerprint=fingerprint(material),
        )

    def verify_fingerprint(self) -> bool:
        material = {
            "sequence": self.sequence,
            "kind": self.kind.value,
            "lifecycle_state": self.lifecycle_state.value,
            "session_id": self.session_id,
            "detail": self.detail,
            "occurred_at": self.occurred_at.isoformat(),
        }
        return fingerprint(material) == self.event_fingerprint


@dataclass(frozen=True, slots=True)
class LifecycleSnapshot:
    lifecycle_state: ExecutiveLifecycleState
    active_session: ExecutiveSession | None
    event_count: int
    snapshot_fingerprint: str

    @classmethod
    def create(
        cls,
        *,
        lifecycle_state: ExecutiveLifecycleState,
        active_session: ExecutiveSession | None,
        event_count: int,
    ) -> "LifecycleSnapshot":
        material = {
            "lifecycle_state": lifecycle_state.value,
            "active_session": (
                active_session.canonical_dict()
                if active_session is not None
                else None
            ),
            "event_count": event_count,
        }
        return cls(
            lifecycle_state=lifecycle_state,
            active_session=active_session,
            event_count=event_count,
            snapshot_fingerprint=fingerprint(material),
        )


__all__ = [
    "ExecutiveLifecycleState",
    "ExecutiveSession",
    "ExecutiveSessionStatus",
    "InvalidLifecycleTransitionError",
    "LifecycleError",
    "LifecycleEvent",
    "LifecycleEventKind",
    "LifecycleSnapshot",
    "SessionAlreadyActiveError",
    "SessionNotActiveError",
    "canonical_json",
    "fingerprint",
    "utc_now",
]
