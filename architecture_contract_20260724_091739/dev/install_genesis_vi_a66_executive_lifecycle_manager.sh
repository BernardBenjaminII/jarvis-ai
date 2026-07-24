#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"

cd "$PROJECT_ROOT"

if [ ! -d "core/executive/persistence" ]; then
    echo "ERROR: Run from the JARVIS repository root."
    echo "Missing: core/executive/persistence"
    exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
    echo "ERROR: Python interpreter is not executable: $PYTHON_BIN"
    exit 1
fi

BACKUP_ROOT=".migration_backups/genesis_vi_a66_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_ROOT"

backup_if_present() {
    local path="$1"
    if [ -f "$path" ]; then
        mkdir -p "$BACKUP_ROOT/$(dirname "$path")"
        cp "$path" "$BACKUP_ROOT/$path"
    fi
}

for path in \
    core/executive/lifecycle/__init__.py \
    core/executive/lifecycle/contracts.py \
    core/executive/lifecycle/manager.py \
    tests/test_genesis_vi_a66_executive_lifecycle.py \
    docs/architecture/genesis_vi_a66_executive_lifecycle_manager.md \
    dev/verification/verify_genesis_vi_a66.py \
    dev/verify_genesis_vi_a66.sh \
    dev/demo_genesis_vi_a66.py
do
    backup_if_present "$path"
done

mkdir -p \
    core/executive/lifecycle \
    tests \
    docs/architecture \
    dev/verification \
    dev

cat > core/executive/lifecycle/contracts.py <<'PY'
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
PY

cat > core/executive/lifecycle/manager.py <<'PY'
"""Genesis VI-A6.6 Executive Lifecycle & Session Manager."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, Mapping, Protocol
from uuid import uuid4

from .contracts import (
    ExecutiveLifecycleState,
    ExecutiveSession,
    ExecutiveSessionStatus,
    InvalidLifecycleTransitionError,
    LifecycleEvent,
    LifecycleEventKind,
    LifecycleSnapshot,
    SessionAlreadyActiveError,
    SessionNotActiveError,
    fingerprint,
    utc_now,
)


class CheckpointWriter(Protocol):
    def __call__(
        self,
        session_id: str,
        executive_state: object,
    ) -> object:
        """Persist one Executive checkpoint and return checkpoint metadata."""


class RecoveryInvoker(Protocol):
    def __call__(
        self,
        session_id: str,
        policy: object | None = None,
    ) -> object:
        """Recover an Executive session and return a recovery result."""


class ExecutiveLifecycleManager:
    """Owns deterministic Executive boot, session, checkpoint, and recovery flow."""

    _ALLOWED: dict[ExecutiveLifecycleState, set[ExecutiveLifecycleState]] = {
        ExecutiveLifecycleState.OFFLINE: {
            ExecutiveLifecycleState.BOOTING,
        },
        ExecutiveLifecycleState.BOOTING: {
            ExecutiveLifecycleState.READY,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.READY: {
            ExecutiveLifecycleState.ACTIVE,
            ExecutiveLifecycleState.RECOVERING,
            ExecutiveLifecycleState.SHUTTING_DOWN,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.ACTIVE: {
            ExecutiveLifecycleState.CHECKPOINTING,
            ExecutiveLifecycleState.SUSPENDED,
            ExecutiveLifecycleState.READY,
            ExecutiveLifecycleState.SHUTTING_DOWN,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.CHECKPOINTING: {
            ExecutiveLifecycleState.ACTIVE,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.RECOVERING: {
            ExecutiveLifecycleState.ACTIVE,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.SUSPENDED: {
            ExecutiveLifecycleState.RECOVERING,
            ExecutiveLifecycleState.SHUTTING_DOWN,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.SHUTTING_DOWN: {
            ExecutiveLifecycleState.OFFLINE,
            ExecutiveLifecycleState.FAILED,
        },
        ExecutiveLifecycleState.FAILED: {
            ExecutiveLifecycleState.SHUTTING_DOWN,
            ExecutiveLifecycleState.OFFLINE,
        },
    }

    def __init__(
        self,
        *,
        checkpoint_writer: CheckpointWriter | None = None,
        recovery_invoker: RecoveryInvoker | None = None,
        session_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._state = ExecutiveLifecycleState.OFFLINE
        self._active_session: ExecutiveSession | None = None
        self._events: list[LifecycleEvent] = []
        self._checkpoint_writer = checkpoint_writer
        self._recovery_invoker = recovery_invoker
        self._session_id_factory = session_id_factory or (
            lambda: f"executive-session-{uuid4().hex}"
        )

    @property
    def state(self) -> ExecutiveLifecycleState:
        return self._state

    @property
    def active_session(self) -> ExecutiveSession | None:
        return self._active_session

    @property
    def events(self) -> tuple[LifecycleEvent, ...]:
        return tuple(self._events)

    def snapshot(self) -> LifecycleSnapshot:
        return LifecycleSnapshot.create(
            lifecycle_state=self._state,
            active_session=self._active_session,
            event_count=len(self._events),
        )

    def boot(self) -> LifecycleSnapshot:
        self._transition(ExecutiveLifecycleState.BOOTING)
        self._record(
            LifecycleEventKind.BOOT_STARTED,
            "Executive boot sequence started.",
        )
        self._transition(ExecutiveLifecycleState.READY)
        self._record(
            LifecycleEventKind.BOOT_COMPLETED,
            "Executive boot sequence completed.",
        )
        return self.snapshot()

    def create_session(
        self,
        *,
        mission_id: str,
        mission_title: str,
        metadata: Mapping[str, object] | None = None,
        activate: bool = True,
    ) -> ExecutiveSession:
        self._require_state(ExecutiveLifecycleState.READY)
        if self._active_session is not None:
            raise SessionAlreadyActiveError(
                f"Session {self._active_session.session_id} is already active."
            )
        now = utc_now()
        session = ExecutiveSession(
            session_id=self._session_id_factory(),
            mission_id=mission_id,
            mission_title=mission_title,
            status=ExecutiveSessionStatus.CREATED,
            created_at=now,
            updated_at=now,
            metadata=dict(metadata or {}),
        )
        self._active_session = session
        self._record(
            LifecycleEventKind.SESSION_CREATED,
            f"Executive session created for mission {mission_id}.",
        )
        if activate:
            self._transition(ExecutiveLifecycleState.ACTIVE)
            self._active_session = session.evolve(
                status=ExecutiveSessionStatus.ACTIVE
            )
            self._record(
                LifecycleEventKind.SESSION_ACTIVATED,
                f"Executive session {session.session_id} activated.",
            )
        return self._active_session

    def checkpoint(self, executive_state: object) -> ExecutiveSession:
        self._require_active_session()
        if self._checkpoint_writer is None:
            raise RuntimeError("No checkpoint writer is configured.")

        self._transition(ExecutiveLifecycleState.CHECKPOINTING)
        self._record(
            LifecycleEventKind.CHECKPOINT_STARTED,
            "Executive checkpoint started.",
        )
        try:
            checkpoint = self._checkpoint_writer(
                self._active_session.session_id,
                executive_state,
            )
            sequence = int(
                getattr(
                    checkpoint,
                    "sequence",
                    self._active_session.checkpoint_sequence + 1,
                )
            )
            checkpoint_id = str(
                getattr(checkpoint, "checkpoint_id", f"checkpoint-{sequence}")
            )
            state_fp = fingerprint(executive_state)
            self._active_session = self._active_session.evolve(
                status=ExecutiveSessionStatus.CHECKPOINTED,
                checkpoint_sequence=sequence,
                last_checkpoint_id=checkpoint_id,
                state_fingerprint=state_fp,
            )
            self._transition(ExecutiveLifecycleState.ACTIVE)
            self._active_session = self._active_session.evolve(
                status=ExecutiveSessionStatus.ACTIVE
            )
            self._record(
                LifecycleEventKind.CHECKPOINT_COMPLETED,
                f"Checkpoint {checkpoint_id} completed.",
            )
            return self._active_session
        except Exception as exc:
            self._state = ExecutiveLifecycleState.FAILED
            self._record(
                LifecycleEventKind.FAILURE_RECORDED,
                f"Checkpoint failed: {type(exc).__name__}.",
            )
            raise

    def suspend(self) -> ExecutiveSession:
        self._require_active_session()
        self._transition(ExecutiveLifecycleState.SUSPENDED)
        self._active_session = self._active_session.evolve(
            status=ExecutiveSessionStatus.SUSPENDED
        )
        self._record(
            LifecycleEventKind.SESSION_SUSPENDED,
            f"Session {self._active_session.session_id} suspended.",
        )
        return self._active_session

    def recover(
        self,
        *,
        session_id: str,
        policy: object | None = None,
        mission_id: str = "recovered-mission",
        mission_title: str = "Recovered Executive Mission",
    ) -> object:
        if self._state not in {
            ExecutiveLifecycleState.READY,
            ExecutiveLifecycleState.SUSPENDED,
        }:
            raise InvalidLifecycleTransitionError(
                f"Recovery is not allowed from {self._state.value}."
            )
        if self._recovery_invoker is None:
            raise RuntimeError("No recovery invoker is configured.")

        self._transition(ExecutiveLifecycleState.RECOVERING)
        self._record(
            LifecycleEventKind.RECOVERY_STARTED,
            f"Recovery started for session {session_id}.",
        )
        try:
            result = self._recovery_invoker(session_id, policy)
            report = getattr(result, "report")
            selected_sequence = int(
                getattr(report, "selected_sequence", 0) or 0
            )
            selected_checkpoint_id = getattr(
                report,
                "selected_checkpoint_id",
                None,
            )
            recovered_state_fp = getattr(
                report,
                "recovered_state_fingerprint",
                None,
            )
            now = utc_now()
            self._active_session = ExecutiveSession(
                session_id=session_id,
                mission_id=mission_id,
                mission_title=mission_title,
                status=ExecutiveSessionStatus.RECOVERED,
                created_at=now,
                updated_at=now,
                checkpoint_sequence=selected_sequence,
                last_checkpoint_id=selected_checkpoint_id,
                state_fingerprint=recovered_state_fp,
            )
            self._transition(ExecutiveLifecycleState.ACTIVE)
            self._active_session = self._active_session.evolve(
                status=ExecutiveSessionStatus.ACTIVE
            )
            self._record(
                LifecycleEventKind.RECOVERY_COMPLETED,
                (
                    f"Session {session_id} recovered from "
                    f"{selected_checkpoint_id}."
                ),
            )
            return result
        except Exception as exc:
            self._state = ExecutiveLifecycleState.FAILED
            self._record(
                LifecycleEventKind.FAILURE_RECORDED,
                f"Recovery failed: {type(exc).__name__}.",
            )
            raise

    def complete_session(self) -> ExecutiveSession:
        self._require_active_session()
        completed = self._active_session.evolve(
            status=ExecutiveSessionStatus.COMPLETED
        )
        self._record(
            LifecycleEventKind.SESSION_COMPLETED,
            f"Session {completed.session_id} completed.",
        )
        self._active_session = None
        self._transition(ExecutiveLifecycleState.READY)
        return completed

    def abort_session(self, reason: str) -> ExecutiveSession:
        if self._active_session is None:
            raise SessionNotActiveError("No Executive session is active.")
        aborted = self._active_session.evolve(
            status=ExecutiveSessionStatus.ABORTED
        )
        self._record(
            LifecycleEventKind.SESSION_ABORTED,
            f"Session {aborted.session_id} aborted: {reason}",
        )
        self._active_session = None
        if self._state is not ExecutiveLifecycleState.READY:
            self._transition(ExecutiveLifecycleState.READY)
        return aborted

    def shutdown(self) -> LifecycleSnapshot:
        if self._state is ExecutiveLifecycleState.OFFLINE:
            return self.snapshot()
        if self._active_session is not None and self._state is (
            ExecutiveLifecycleState.ACTIVE
        ):
            self.suspend()
        self._transition(ExecutiveLifecycleState.SHUTTING_DOWN)
        self._record(
            LifecycleEventKind.SHUTDOWN_STARTED,
            "Executive shutdown started.",
        )
        self._transition(ExecutiveLifecycleState.OFFLINE)
        self._record(
            LifecycleEventKind.SHUTDOWN_COMPLETED,
            "Executive shutdown completed.",
        )
        return self.snapshot()

    def _transition(self, target: ExecutiveLifecycleState) -> None:
        allowed = self._ALLOWED[self._state]
        if target not in allowed:
            raise InvalidLifecycleTransitionError(
                f"Transition {self._state.value} -> {target.value} "
                "is not permitted."
            )
        self._state = target

    def _require_state(self, required: ExecutiveLifecycleState) -> None:
        if self._state is not required:
            raise InvalidLifecycleTransitionError(
                f"Operation requires {required.value}; "
                f"current state is {self._state.value}."
            )

    def _require_active_session(self) -> None:
        self._require_state(ExecutiveLifecycleState.ACTIVE)
        if self._active_session is None:
            raise SessionNotActiveError("No Executive session is active.")

    def _record(
        self,
        kind: LifecycleEventKind,
        detail: str,
    ) -> LifecycleEvent:
        event = LifecycleEvent.create(
            sequence=len(self._events) + 1,
            kind=kind,
            lifecycle_state=self._state,
            session_id=(
                self._active_session.session_id
                if self._active_session is not None
                else None
            ),
            detail=detail,
        )
        self._events.append(event)
        return event


__all__ = [
    "CheckpointWriter",
    "ExecutiveLifecycleManager",
    "RecoveryInvoker",
]
PY

cat > core/executive/lifecycle/__init__.py <<'PY'
"""Public Genesis VI-A6.6 Executive lifecycle API."""

from .contracts import (
    ExecutiveLifecycleState,
    ExecutiveSession,
    ExecutiveSessionStatus,
    InvalidLifecycleTransitionError,
    LifecycleError,
    LifecycleEvent,
    LifecycleEventKind,
    LifecycleSnapshot,
    SessionAlreadyActiveError,
    SessionNotActiveError,
)
from .manager import (
    CheckpointWriter,
    ExecutiveLifecycleManager,
    RecoveryInvoker,
)

__all__ = [
    "CheckpointWriter",
    "ExecutiveLifecycleManager",
    "ExecutiveLifecycleState",
    "ExecutiveSession",
    "ExecutiveSessionStatus",
    "InvalidLifecycleTransitionError",
    "LifecycleError",
    "LifecycleEvent",
    "LifecycleEventKind",
    "LifecycleSnapshot",
    "RecoveryInvoker",
    "SessionAlreadyActiveError",
    "SessionNotActiveError",
]
PY

cat > tests/test_genesis_vi_a66_executive_lifecycle.py <<'PY'
from __future__ import annotations

from dataclasses import dataclass
import unittest

from core.executive.lifecycle import (
    ExecutiveLifecycleManager,
    ExecutiveLifecycleState,
    ExecutiveSessionStatus,
    InvalidLifecycleTransitionError,
    LifecycleEventKind,
)


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    sequence: int


@dataclass(frozen=True)
class RecoveryReport:
    selected_checkpoint_id: str
    selected_sequence: int
    recovered_state_fingerprint: str


@dataclass(frozen=True)
class RecoveryResult:
    state: object
    report: RecoveryReport


class CheckpointWriter:
    def __init__(self) -> None:
        self.sequence = 0

    def __call__(self, session_id: str, state: object) -> Checkpoint:
        self.sequence += 1
        return Checkpoint(
            checkpoint_id=f"{session_id}-cp-{self.sequence}",
            sequence=self.sequence,
        )


def recovery_invoker(
    session_id: str,
    policy: object | None = None,
) -> RecoveryResult:
    return RecoveryResult(
        state={"mission": "Recovered", "step": 3},
        report=RecoveryReport(
            selected_checkpoint_id="checkpoint-0003",
            selected_sequence=3,
            recovered_state_fingerprint="abc123",
        ),
    )


class Tests(unittest.TestCase):
    def manager(self) -> ExecutiveLifecycleManager:
        return ExecutiveLifecycleManager(
            checkpoint_writer=CheckpointWriter(),
            recovery_invoker=recovery_invoker,
            session_id_factory=lambda: "executive-session-test",
        )

    def test_boot_reaches_ready(self) -> None:
        manager = self.manager()
        snapshot = manager.boot()
        self.assertEqual(
            snapshot.lifecycle_state,
            ExecutiveLifecycleState.READY,
        )
        self.assertEqual(len(manager.events), 2)

    def test_session_creation_activates(self) -> None:
        manager = self.manager()
        manager.boot()
        session = manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        self.assertEqual(manager.state, ExecutiveLifecycleState.ACTIVE)
        self.assertEqual(session.status, ExecutiveSessionStatus.ACTIVE)

    def test_checkpoint_updates_session(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        session = manager.checkpoint({"step": 1})
        self.assertEqual(session.checkpoint_sequence, 1)
        self.assertIsNotNone(session.state_fingerprint)
        self.assertEqual(manager.state, ExecutiveLifecycleState.ACTIVE)

    def test_suspend(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        session = manager.suspend()
        self.assertEqual(session.status, ExecutiveSessionStatus.SUSPENDED)
        self.assertEqual(
            manager.state,
            ExecutiveLifecycleState.SUSPENDED,
        )

    def test_recovery_reactivates_session(self) -> None:
        manager = self.manager()
        manager.boot()
        result = manager.recover(session_id="executive-session-old")
        self.assertEqual(result.state["step"], 3)
        self.assertEqual(manager.state, ExecutiveLifecycleState.ACTIVE)
        self.assertEqual(
            manager.active_session.checkpoint_sequence,
            3,
        )

    def test_complete_returns_to_ready(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        completed = manager.complete_session()
        self.assertEqual(
            completed.status,
            ExecutiveSessionStatus.COMPLETED,
        )
        self.assertEqual(manager.state, ExecutiveLifecycleState.READY)
        self.assertIsNone(manager.active_session)

    def test_shutdown_suspends_active_session(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        snapshot = manager.shutdown()
        self.assertEqual(
            snapshot.lifecycle_state,
            ExecutiveLifecycleState.OFFLINE,
        )
        self.assertEqual(
            manager.active_session.status,
            ExecutiveSessionStatus.SUSPENDED,
        )

    def test_invalid_transition_refused(self) -> None:
        manager = self.manager()
        with self.assertRaises(InvalidLifecycleTransitionError):
            manager.create_session(
                mission_id="mission-1",
                mission_title="Demonstrate lifecycle",
            )

    def test_event_fingerprints_verify(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        manager.checkpoint({"step": 1})
        self.assertTrue(all(event.verify_fingerprint() for event in manager.events))

    def test_event_sequence_is_monotonic(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        sequences = [event.sequence for event in manager.events]
        self.assertEqual(sequences, list(range(1, len(sequences) + 1)))

    def test_checkpoint_event_order(self) -> None:
        manager = self.manager()
        manager.boot()
        manager.create_session(
            mission_id="mission-1",
            mission_title="Demonstrate lifecycle",
        )
        manager.checkpoint({"step": 1})
        kinds = [event.kind for event in manager.events]
        self.assertIn(LifecycleEventKind.CHECKPOINT_STARTED, kinds)
        self.assertIn(LifecycleEventKind.CHECKPOINT_COMPLETED, kinds)

    def test_snapshot_fingerprint_is_deterministic(self) -> None:
        manager = self.manager()
        manager.boot()
        first = manager.snapshot()
        second = manager.snapshot()
        self.assertEqual(
            first.snapshot_fingerprint,
            second.snapshot_fingerprint,
        )


if __name__ == "__main__":
    unittest.main()
PY

cat > docs/architecture/genesis_vi_a66_executive_lifecycle_manager.md <<'MD'
# Genesis VI-A6.6 — Executive Lifecycle & Session Manager

**Status:** Implemented  
**Layer:** Executive Continuity  
**Depends on:** Genesis VI-A6.1 through VI-A6.5

## Purpose

Genesis VI-A6.6 introduces the conductor for the Executive continuity stack.

It owns:

- Executive boot,
- readiness,
- session creation,
- mission activation,
- checkpoint coordination,
- suspension,
- certified recovery invocation,
- mission resumption,
- completion,
- abort,
- orderly shutdown.

## Lifecycle

```text
OFFLINE
   ↓
BOOTING
   ↓
READY
   ↓
ACTIVE
   ├── CHECKPOINTING ──→ ACTIVE
   ├── SUSPENDED ──→ RECOVERING ──→ ACTIVE
   ├── READY
   └── SHUTTING_DOWN ──→ OFFLINE
```

Failures transition the manager to `FAILED`.

## Architectural Boundary

The lifecycle manager coordinates but does not duplicate lower-level work.

It does not:

- serialize Executive state,
- write checkpoint files directly,
- validate cryptographic integrity,
- select recovery points internally,
- reconstruct state itself.

Those responsibilities remain in Genesis VI-A6.2 through VI-A6.5.

## Event Evidence

Every lifecycle action produces an immutable event containing:

- monotonic sequence,
- event kind,
- lifecycle state,
- session identifier,
- detail,
- timestamp,
- event fingerprint.

These events are the future source for:

- Mission Control status panels,
- the Executive timeline,
- recovery prompts,
- audit views,
- deterministic replay.

## UI Relationship

Mission Control should consume lifecycle state rather than inventing it.

Examples:

```text
READY        → Executive Online
ACTIVE       → Mission Active
CHECKPOINTING→ Saving Executive State
SUSPENDED    → Mission Interrupted
RECOVERING   → Restoring Certified Session
FAILED       → Executive Intervention Required
OFFLINE      → Executive Offline
```

This phase establishes the authoritative backend state machine that the UI will
visualize.
MD

cat > dev/verification/verify_genesis_vi_a66.py <<'PY'
#!/usr/bin/env python3
"""Structural certification for Genesis VI-A6.6."""

from __future__ import annotations

from hashlib import sha256
import inspect
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    ROOT / "core/executive/lifecycle/__init__.py",
    ROOT / "core/executive/lifecycle/contracts.py",
    ROOT / "core/executive/lifecycle/manager.py",
    ROOT / "tests/test_genesis_vi_a66_executive_lifecycle.py",
    ROOT / "docs/architecture/genesis_vi_a66_executive_lifecycle_manager.md",
    ROOT / "dev/verify_genesis_vi_a66.sh",
)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    missing = [
        str(path.relative_to(ROOT))
        for path in REQUIRED
        if not path.is_file()
    ]
    if missing:
        fail(f"Missing files: {', '.join(missing)}")
    print("[PASS] Canonical Genesis VI-A6.6 structure")

    sys.path.insert(0, str(ROOT))
    from core.executive.lifecycle import (
        ExecutiveLifecycleManager,
        ExecutiveLifecycleState,
        ExecutiveSession,
        LifecycleEvent,
        LifecycleSnapshot,
    )

    for public_type in (
        ExecutiveLifecycleManager,
        ExecutiveLifecycleState,
        ExecutiveSession,
        LifecycleEvent,
        LifecycleSnapshot,
    ):
        if not inspect.isclass(public_type):
            fail(f"{public_type!r} is not a stable public type.")
    print("[PASS] Stable Executive lifecycle public API")

    source = inspect.getsource(ExecutiveLifecycleManager)
    required_concepts = (
        "checkpoint_writer",
        "recovery_invoker",
        "CHECKPOINTING",
        "RECOVERING",
        "SUSPENDED",
    )
    for concept in required_concepts:
        if concept not in source:
            fail(f"Lifecycle manager is missing concept: {concept}")
    print("[PASS] Checkpoint and recovery orchestration boundaries")

    if "open(" in source or "sqlite" in source.lower():
        fail("Lifecycle manager performs direct storage operations.")
    print("[PASS] Storage-free lifecycle coordination")

    digest = sha256(
        (
            REQUIRED[1].read_bytes()
            + REQUIRED[2].read_bytes()
        )
    ).hexdigest()
    print(f"[PASS] Deterministic architecture fingerprint: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > dev/verify_genesis_vi_a66.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"

cd "$PROJECT_ROOT"

checks_failed=0

run_check() {
    local label="$1"
    shift
    if "$@"; then
        echo "[PASS] $label"
    else
        echo "[FAIL] $label"
        checks_failed=$((checks_failed + 1))
    fi
}

echo
echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.6 EXECUTIVE LIFECYCLE & SESSION MANAGER"
echo "========================================================================"

run_check \
    "Genesis VI-A6.6 package compilation" \
    "$PYTHON_BIN" -m compileall -q core/executive/lifecycle

run_check \
    "Genesis VI-A6.6 unit tests" \
    env PYTHONPATH="$PROJECT_ROOT" \
    "$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_vi_a66_executive_lifecycle

run_check \
    "Genesis VI-A6.6 structural verification" \
    env PYTHONPATH="$PROJECT_ROOT" \
    "$PYTHON_BIN" dev/verification/verify_genesis_vi_a66.py

for regression in \
    dev/verify_genesis_vi_a65.sh \
    dev/verify_genesis_vi_a64.sh \
    dev/verify_genesis_vi_a63.sh
do
    if [ -x "$regression" ]; then
        run_check \
            "Regression: $(basename "$regression")" \
            env PYTHONPATH="$PROJECT_ROOT" \
            PYTHON_BIN="$PYTHON_BIN" \
            "$regression"
    else
        echo "[SKIP] Regression wrapper absent: $regression"
    fi
done

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : $checks_failed"

if [ "$checks_failed" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
else
    echo "Overall status: FAILED"
fi

echo "========================================================================"

exit "$checks_failed"
SH

cat > dev/demo_genesis_vi_a66.py <<'PY'
#!/usr/bin/env python3
"""Interactive lifecycle demonstration for Genesis VI-A6.6."""

from __future__ import annotations

from dataclasses import dataclass

from core.executive.lifecycle import ExecutiveLifecycleManager


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    sequence: int


@dataclass(frozen=True)
class RecoveryReport:
    selected_checkpoint_id: str
    selected_sequence: int
    recovered_state_fingerprint: str


@dataclass(frozen=True)
class RecoveryResult:
    state: object
    report: RecoveryReport


class DemoCheckpointWriter:
    def __init__(self) -> None:
        self.sequence = 0

    def __call__(self, session_id: str, state: object) -> Checkpoint:
        self.sequence += 1
        return Checkpoint(
            checkpoint_id=f"checkpoint-{self.sequence:04d}",
            sequence=self.sequence,
        )


def demo_recovery(
    session_id: str,
    policy: object | None = None,
) -> RecoveryResult:
    return RecoveryResult(
        state={
            "mission": "Investigate suspicious network activity",
            "completed_steps": 2,
            "status": "active",
        },
        report=RecoveryReport(
            selected_checkpoint_id="checkpoint-0002",
            selected_sequence=2,
            recovered_state_fingerprint="certified-recovered-state",
        ),
    )


def show(manager: ExecutiveLifecycleManager, title: str) -> None:
    snapshot = manager.snapshot()
    session = snapshot.active_session

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)
    print(f"Executive state : {snapshot.lifecycle_state.value.upper()}")
    print(f"Events          : {snapshot.event_count}")
    print(f"Snapshot        : {snapshot.snapshot_fingerprint}")

    if session is None:
        print("Session         : NONE")
        return

    print(f"Session         : {session.session_id}")
    print(f"Mission         : {session.mission_title}")
    print(f"Session status  : {session.status.value.upper()}")
    print(f"Checkpoint      : {session.last_checkpoint_id}")
    print(f"Sequence        : {session.checkpoint_sequence}")


def main() -> int:
    manager = ExecutiveLifecycleManager(
        checkpoint_writer=DemoCheckpointWriter(),
        recovery_invoker=demo_recovery,
        session_id_factory=lambda: "executive-session-demo",
    )

    manager.boot()
    show(manager, "SCENARIO 1 — EXECUTIVE BOOT")

    manager.create_session(
        mission_id="mission-network-001",
        mission_title="Investigate suspicious network activity",
    )
    show(manager, "SCENARIO 2 — MISSION ACTIVATED")

    manager.checkpoint(
        {
            "mission": "Investigate suspicious network activity",
            "completed_steps": 1,
            "status": "active",
        }
    )
    show(manager, "SCENARIO 3 — EXECUTIVE CHECKPOINT")

    manager.suspend()
    show(manager, "SCENARIO 4 — SIMULATED INTERRUPTION")

    manager.shutdown()
    show(manager, "SCENARIO 5 — EXECUTIVE OFFLINE")

    recovered = ExecutiveLifecycleManager(
        checkpoint_writer=DemoCheckpointWriter(),
        recovery_invoker=demo_recovery,
        session_id_factory=lambda: "unused",
    )
    recovered.boot()
    recovery_result = recovered.recover(
        session_id="executive-session-demo",
        mission_id="mission-network-001",
        mission_title="Investigate suspicious network activity",
    )
    show(recovered, "SCENARIO 6 — CERTIFIED MISSION RESUMPTION")

    print()
    print("Recovered state:")
    for key, value in recovery_result.state.items():
        print(f"  {key:<18}: {value}")

    print()
    print("=" * 78)
    print("EXECUTIVE TIMELINE")
    print("=" * 78)
    for event in recovered.events:
        print(
            f"{event.sequence:02d}  "
            f"{event.kind.value:<24} "
            f"{event.lifecycle_state.value:<12} "
            f"{event.detail}"
        )

    print()
    print("=" * 78)
    print("GENESIS VI-A6.6 TEST DRIVE COMPLETE")
    print("=" * 78)
    print("The Executive can now boot, run, suspend, recover, and resume missions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x \
    dev/install_genesis_vi_a66_executive_lifecycle_manager.sh \
    dev/verification/verify_genesis_vi_a66.py \
    dev/verify_genesis_vi_a66.sh \
    dev/demo_genesis_vi_a66.py

echo
echo "Installed Genesis VI-A6.6."
echo "Backup: $BACKUP_ROOT"
echo
echo "Verify:"
echo "  PYTHON_BIN=$PYTHON_BIN ./dev/verify_genesis_vi_a66.sh"
echo
echo "Demo:"
echo "  PYTHONPATH=\"\$(pwd)\" $PYTHON_BIN dev/demo_genesis_vi_a66.py"
