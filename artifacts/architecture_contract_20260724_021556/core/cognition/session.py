"""Executive-session ownership for Genesis VI-A5."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Callable, Dict, Iterable, Mapping, Tuple

from .cycle import CognitionCycleController, CognitionCycleSnapshot
from .enums import CognitiveState
from .models import ExecutiveContext, MemoryEntry, utc_now
from .state_machine import DEFAULT_TRANSITION_POLICY, TransitionPolicy


class ExecutiveSessionStatus(str, Enum):
    """Lifecycle status of one executive session."""

    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ExecutiveSessionEvent:
    """Immutable session-level audit event."""

    sequence: int
    kind: str
    message: str
    occurred_at: datetime
    cycle_id: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("sequence must be at least 1")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        if not self.message.strip():
            raise ValueError("message must not be empty")


@dataclass(frozen=True, slots=True)
class ExecutiveSessionSnapshot:
    """Immutable complete projection of an executive session."""

    session_id: str
    mission_id: str
    executive_id: str
    authority: str
    status: ExecutiveSessionStatus
    active_cycle_id: str | None
    cycles: Tuple[CognitionCycleSnapshot, ...]
    events: Tuple[ExecutiveSessionEvent, ...]
    created_at: datetime
    updated_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")
        if not self.mission_id.strip():
            raise ValueError("mission_id must not be empty")
        if not self.executive_id.strip():
            raise ValueError("executive_id must not be empty")
        if not self.authority.strip():
            raise ValueError("authority must not be empty")
        cycle_ids = tuple(item.context.cycle_id for item in self.cycles)
        if len(cycle_ids) != len(set(cycle_ids)):
            raise ValueError("cycle identifiers must be unique")
        if self.active_cycle_id is not None and self.active_cycle_id not in cycle_ids:
            raise ValueError("active_cycle_id must identify a session cycle")
        object.__setattr__(self, "metadata", MappingProxyType(dict(sorted(self.metadata.items()))))


class ExecutiveSession:
    """Authoritative mission-scoped owner of cognition cycles.

    A session supplies stable executive and mission identity, admits cognition
    cycles, guarantees that at most one cycle is active, and retains completed,
    failed, or suspended cycle history for the lifetime of the process.
    """

    def __init__(
        self,
        *,
        session_id: str,
        mission_id: str,
        executive_id: str,
        authority: str,
        metadata: Mapping[str, str] | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        for label, value in (
            ("session_id", session_id),
            ("mission_id", mission_id),
            ("executive_id", executive_id),
            ("authority", authority),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")
        self._session_id = session_id
        self._mission_id = mission_id
        self._executive_id = executive_id
        self._authority = authority
        self._metadata = dict(metadata or {})
        self._clock = clock
        self._created_at = clock()
        self._updated_at = self._created_at
        self._status = ExecutiveSessionStatus.CREATED
        self._active_cycle_id: str | None = None
        self._cycles: Dict[str, CognitionCycleController] = {}
        self._events: list[ExecutiveSessionEvent] = []
        self._emit("session_created", f"Created executive session {session_id}.")

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def mission_id(self) -> str:
        return self._mission_id

    @property
    def executive_id(self) -> str:
        return self._executive_id

    @property
    def status(self) -> ExecutiveSessionStatus:
        return self._status

    @property
    def active_cycle_id(self) -> str | None:
        return self._active_cycle_id

    def _require_open(self) -> None:
        if self._status is ExecutiveSessionStatus.CLOSED:
            raise RuntimeError(f"executive session is closed: {self._session_id}")

    def _emit(self, kind: str, message: str, cycle_id: str | None = None) -> None:
        timestamp = self._clock()
        self._updated_at = timestamp
        self._events.append(
            ExecutiveSessionEvent(
                sequence=len(self._events) + 1,
                kind=kind,
                message=message,
                occurred_at=timestamp,
                cycle_id=cycle_id,
            )
        )

    def create_cycle(
        self,
        *,
        cycle_id: str,
        goal: str,
        objective_id: str | None = None,
        task_id: str | None = None,
        constraints: Iterable[str] = (),
        memory_capacity: int = 32,
        policy: TransitionPolicy = DEFAULT_TRANSITION_POLICY,
    ) -> ExecutiveContext:
        """Create a session-owned cycle without activating it."""

        self._require_open()
        if cycle_id in self._cycles:
            raise ValueError(f"duplicate cycle_id: {cycle_id}")
        controller = CognitionCycleController(
            cycle_id=cycle_id,
            mission_id=self._mission_id,
            goal=goal,
            authority=self._authority,
            objective_id=objective_id,
            task_id=task_id,
            constraints=tuple(constraints),
            memory_capacity=memory_capacity,
            policy=policy,
            clock=self._clock,
        )
        self._cycles[cycle_id] = controller
        self._emit("cycle_created", f"Created cognition cycle {cycle_id}.", cycle_id)
        return controller.context

    def _cycle(self, cycle_id: str) -> CognitionCycleController:
        try:
            return self._cycles[cycle_id]
        except KeyError as exc:
            raise KeyError(f"unknown session cycle: {cycle_id}") from exc

    def cycle_snapshot(self, cycle_id: str) -> CognitionCycleSnapshot:
        return self._cycle(cycle_id).snapshot()

    def start_cycle(self, cycle_id: str, *, reason: str = "Begin cognition cycle.") -> ExecutiveContext:
        """Activate one cycle while enforcing single-active-cycle ownership."""

        self._require_open()
        if self._active_cycle_id is not None and self._active_cycle_id != cycle_id:
            raise RuntimeError(
                "another cognition cycle is active: " + self._active_cycle_id
            )
        cycle = self._cycle(cycle_id)
        context = cycle.start(reason=reason)
        self._active_cycle_id = cycle_id
        self._status = ExecutiveSessionStatus.ACTIVE
        self._emit("cycle_started", reason, cycle_id)
        return context

    def advance_cycle(self, cycle_id: str, next_state: CognitiveState, *, reason: str) -> ExecutiveContext:
        self._require_open()
        if self._active_cycle_id != cycle_id:
            raise RuntimeError(f"cycle is not the active session cycle: {cycle_id}")
        context = self._cycle(cycle_id).advance(next_state, reason=reason)
        self._emit("cycle_advanced", reason, cycle_id)
        return context

    def admit_memory(self, cycle_id: str, entry: MemoryEntry) -> MemoryEntry | None:
        self._require_open()
        if self._active_cycle_id != cycle_id:
            raise RuntimeError(f"cycle is not the active session cycle: {cycle_id}")
        evicted = self._cycle(cycle_id).admit_memory(entry)
        self._emit("memory_admitted", f"Admitted memory {entry.entry_id}.", cycle_id)
        return evicted

    def record_note(self, cycle_id: str, note: str) -> ExecutiveContext:
        self._require_open()
        if self._active_cycle_id != cycle_id:
            raise RuntimeError(f"cycle is not the active session cycle: {cycle_id}")
        context = self._cycle(cycle_id).record_note(note)
        self._emit("note_recorded", note, cycle_id)
        return context

    def suspend_cycle(self, cycle_id: str, *, reason: str) -> ExecutiveContext:
        self._require_open()
        if self._active_cycle_id != cycle_id:
            raise RuntimeError(f"cycle is not the active session cycle: {cycle_id}")
        context = self._cycle(cycle_id).suspend(reason=reason)
        self._active_cycle_id = None
        self._status = ExecutiveSessionStatus.SUSPENDED
        self._emit("cycle_suspended", reason, cycle_id)
        return context

    def fail_cycle(self, cycle_id: str, *, reason: str) -> ExecutiveContext:
        self._require_open()
        cycle = self._cycle(cycle_id)
        context = cycle.fail(reason=reason)
        if self._active_cycle_id == cycle_id:
            self._active_cycle_id = None
        self._status = ExecutiveSessionStatus.SUSPENDED
        self._emit("cycle_failed", reason, cycle_id)
        return context

    def complete_cycle(self, cycle_id: str, *, reason: str = "Cognition cycle completed.") -> ExecutiveContext:
        self._require_open()
        if self._active_cycle_id != cycle_id:
            raise RuntimeError(f"cycle is not the active session cycle: {cycle_id}")
        context = self._cycle(cycle_id).complete(reason=reason)
        self._active_cycle_id = None
        self._status = ExecutiveSessionStatus.SUSPENDED
        self._emit("cycle_completed", reason, cycle_id)
        return context

    def close(self, *, reason: str = "Executive session closed.") -> ExecutiveSessionSnapshot:
        """Close a session only when it has no active cognition cycle."""

        self._require_open()
        if self._active_cycle_id is not None:
            raise RuntimeError("cannot close a session with an active cycle")
        self._status = ExecutiveSessionStatus.CLOSED
        self._emit("session_closed", reason)
        return self.snapshot()

    def snapshot(self) -> ExecutiveSessionSnapshot:
        cycles = tuple(
            self._cycles[cycle_id].snapshot()
            for cycle_id in sorted(self._cycles)
        )
        return ExecutiveSessionSnapshot(
            session_id=self._session_id,
            mission_id=self._mission_id,
            executive_id=self._executive_id,
            authority=self._authority,
            status=self._status,
            active_cycle_id=self._active_cycle_id,
            cycles=cycles,
            events=tuple(self._events),
            created_at=self._created_at,
            updated_at=self._updated_at,
            metadata=self._metadata,
        )
