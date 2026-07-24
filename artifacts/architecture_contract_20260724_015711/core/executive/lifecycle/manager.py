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
