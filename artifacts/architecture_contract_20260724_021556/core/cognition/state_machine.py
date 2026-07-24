"""Deterministic cognitive lifecycle control for Genesis VI-A3."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Callable, Iterable, Mapping, Tuple

from .enums import CognitiveEventKind, CognitiveState
from .errors import InvalidStateTransitionError
from .models import CognitiveEvent, StateTransition, utc_now


TransitionGuard = Callable[[CognitiveState, CognitiveState], bool]


def _freeze_transition_map(
    transitions: Mapping[CognitiveState, Iterable[CognitiveState]],
) -> Mapping[CognitiveState, Tuple[CognitiveState, ...]]:
    """Return an immutable deterministic transition map."""

    normalized = {
        state: tuple(sorted(set(next_states), key=lambda item: item.value))
        for state, next_states in sorted(
            transitions.items(),
            key=lambda item: item[0].value,
        )
    }
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class TransitionPolicy:
    """Immutable policy defining legal cognitive-state transitions."""

    transitions: Mapping[CognitiveState, Tuple[CognitiveState, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "transitions",
            _freeze_transition_map(self.transitions),
        )

    def allowed_from(
        self,
        state: CognitiveState,
    ) -> Tuple[CognitiveState, ...]:
        """Return legal destination states for ``state``."""

        return self.transitions.get(state, ())

    def permits(
        self,
        previous_state: CognitiveState,
        next_state: CognitiveState,
    ) -> bool:
        """Return whether a transition is permitted."""

        return next_state in self.allowed_from(previous_state)

    def validate(
        self,
        previous_state: CognitiveState,
        next_state: CognitiveState,
    ) -> None:
        """Raise when a transition is not permitted."""

        if previous_state is next_state:
            raise InvalidStateTransitionError(
                f"self-transition is not permitted: {previous_state.value}"
            )

        if not self.permits(previous_state, next_state):
            allowed = ", ".join(
                state.value for state in self.allowed_from(previous_state)
            ) or "<none>"
            raise InvalidStateTransitionError(
                "invalid cognitive-state transition: "
                f"{previous_state.value} -> {next_state.value}; "
                f"allowed: {allowed}"
            )


DEFAULT_TRANSITION_POLICY = TransitionPolicy(
    transitions={
        CognitiveState.IDLE: (
            CognitiveState.INITIALIZING,
        ),
        CognitiveState.INITIALIZING: (
            CognitiveState.OBSERVING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.OBSERVING: (
            CognitiveState.ATTENDING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.ATTENDING: (
            CognitiveState.RETRIEVING,
            CognitiveState.REASONING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.RETRIEVING: (
            CognitiveState.REASONING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.REASONING: (
            CognitiveState.EVALUATING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.EVALUATING: (
            CognitiveState.OBSERVING,
            CognitiveState.RETRIEVING,
            CognitiveState.PLANNING,
            CognitiveState.AWAITING_AUTHORITY,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.PLANNING: (
            CognitiveState.AWAITING_AUTHORITY,
            CognitiveState.EXECUTING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.AWAITING_AUTHORITY: (
            CognitiveState.PLANNING,
            CognitiveState.EXECUTING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.EXECUTING: (
            CognitiveState.OBSERVING,
            CognitiveState.REFLECTING,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.REFLECTING: (
            CognitiveState.OBSERVING,
            CognitiveState.COMPLETED,
            CognitiveState.FAILED,
            CognitiveState.SUSPENDED,
        ),
        CognitiveState.SUSPENDED: (
            CognitiveState.INITIALIZING,
            CognitiveState.OBSERVING,
            CognitiveState.ATTENDING,
            CognitiveState.RETRIEVING,
            CognitiveState.REASONING,
            CognitiveState.EVALUATING,
            CognitiveState.PLANNING,
            CognitiveState.AWAITING_AUTHORITY,
            CognitiveState.EXECUTING,
            CognitiveState.REFLECTING,
            CognitiveState.FAILED,
        ),
        CognitiveState.FAILED: (
            CognitiveState.INITIALIZING,
            CognitiveState.REFLECTING,
        ),
        CognitiveState.COMPLETED: (),
    }
)


@dataclass(frozen=True, slots=True)
class StateMachineSnapshot:
    """Immutable state-machine snapshot suitable for audit and replay."""

    current_state: CognitiveState
    transitions: Tuple[StateTransition, ...]
    events: Tuple[CognitiveEvent, ...]

    @property
    def transition_count(self) -> int:
        return len(self.transitions)

    @property
    def event_count(self) -> int:
        return len(self.events)


class CognitiveStateMachine:
    """Authoritative deterministic controller of executive cognitive state."""

    def __init__(
        self,
        *,
        initial_state: CognitiveState = CognitiveState.IDLE,
        policy: TransitionPolicy = DEFAULT_TRANSITION_POLICY,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._state = initial_state
        self._policy = policy
        self._clock = clock
        self._transitions: list[StateTransition] = []
        self._events: list[CognitiveEvent] = []

    @property
    def current_state(self) -> CognitiveState:
        return self._state

    @property
    def policy(self) -> TransitionPolicy:
        return self._policy

    @property
    def transition_count(self) -> int:
        return len(self._transitions)

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def is_terminal(self) -> bool:
        return not self._policy.allowed_from(self._state)

    def allowed_transitions(self) -> Tuple[CognitiveState, ...]:
        """Return legal next states from the current state."""

        return self._policy.allowed_from(self._state)

    def can_transition_to(self, next_state: CognitiveState) -> bool:
        """Return whether ``next_state`` is legal from the current state."""

        return self._policy.permits(self._state, next_state)

    def transition_to(
        self,
        next_state: CognitiveState,
        *,
        reason: str,
        guard: TransitionGuard | None = None,
    ) -> StateTransition:
        """Validate and record one authoritative state transition."""

        if not reason.strip():
            raise ValueError("reason must not be empty")

        previous_state = self._state
        self._policy.validate(previous_state, next_state)

        if guard is not None and not guard(previous_state, next_state):
            raise InvalidStateTransitionError(
                "transition guard rejected cognitive-state transition: "
                f"{previous_state.value} -> {next_state.value}"
            )

        occurred_at = self._clock()
        sequence = self.transition_count + 1
        transition = StateTransition(
            sequence=sequence,
            previous_state=previous_state,
            next_state=next_state,
            reason=reason,
            occurred_at=occurred_at,
        )
        event = CognitiveEvent(
            sequence=self.event_count + 1,
            kind=CognitiveEventKind.STATE_CHANGED,
            message=(
                f"Cognitive state changed from {previous_state.value} "
                f"to {next_state.value}: {reason}"
            ),
            state=next_state,
            occurred_at=occurred_at,
            metadata={
                "previous_state": previous_state.value,
                "next_state": next_state.value,
                "transition_sequence": sequence,
            },
        )

        self._state = next_state
        self._transitions.append(transition)
        self._events.append(event)
        return transition

    def transition_path(
        self,
        states: Iterable[CognitiveState],
        *,
        reason_prefix: str,
    ) -> Tuple[StateTransition, ...]:
        """Apply a deterministic ordered path of state transitions."""

        if not reason_prefix.strip():
            raise ValueError("reason_prefix must not be empty")

        applied = []
        for index, state in enumerate(states, start=1):
            applied.append(
                self.transition_to(
                    state,
                    reason=f"{reason_prefix} [{index}]",
                )
            )
        return tuple(applied)

    def transitions(self) -> Tuple[StateTransition, ...]:
        """Return immutable transition history."""

        return tuple(self._transitions)

    def events(self) -> Tuple[CognitiveEvent, ...]:
        """Return immutable lifecycle-event history."""

        return tuple(self._events)

    def snapshot(self) -> StateMachineSnapshot:
        """Return an immutable audit snapshot."""

        return StateMachineSnapshot(
            current_state=self.current_state,
            transitions=self.transitions(),
            events=self.events(),
        )

    @classmethod
    def replay(
        cls,
        transitions: Iterable[StateTransition],
        *,
        initial_state: CognitiveState = CognitiveState.IDLE,
        policy: TransitionPolicy = DEFAULT_TRANSITION_POLICY,
        clock: Callable[[], datetime] = utc_now,
    ) -> "CognitiveStateMachine":
        """Reconstruct and validate a machine from transition history."""

        machine = cls(
            initial_state=initial_state,
            policy=policy,
            clock=clock,
        )

        for expected_sequence, transition in enumerate(transitions, start=1):
            if transition.sequence != expected_sequence:
                raise InvalidStateTransitionError(
                    "transition replay sequence mismatch: "
                    f"expected {expected_sequence}, got {transition.sequence}"
                )
            if transition.previous_state is not machine.current_state:
                raise InvalidStateTransitionError(
                    "transition replay state mismatch: "
                    f"machine={machine.current_state.value}, "
                    f"record={transition.previous_state.value}"
                )

            machine._policy.validate(
                transition.previous_state,
                transition.next_state,
            )
            machine._state = transition.next_state
            machine._transitions.append(transition)
            machine._events.append(
                CognitiveEvent(
                    sequence=machine.event_count + 1,
                    kind=CognitiveEventKind.STATE_CHANGED,
                    message=(
                        "Replayed cognitive state change from "
                        f"{transition.previous_state.value} to "
                        f"{transition.next_state.value}: "
                        f"{transition.reason}"
                    ),
                    state=transition.next_state,
                    occurred_at=transition.occurred_at,
                    metadata={
                        "previous_state": transition.previous_state.value,
                        "next_state": transition.next_state.value,
                        "transition_sequence": transition.sequence,
                        "replayed": True,
                    },
                )
            )

        return machine
