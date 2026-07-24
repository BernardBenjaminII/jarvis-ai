"""Deterministic immutable lifecycle for Genesis II reasoning sessions."""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from types import MappingProxyType
from typing import Final, Mapping

from core.reasoning.session.contracts import (
    ReasoningSession,
    ReasoningSessionState,
)
from core.reasoning.session.errors import (
    InvalidReasoningSessionTransitionError,
    ReasoningSessionContractError,
    TerminalReasoningSessionError,
)


TRANSITION_MAP: Final[
    Mapping[ReasoningSessionState, frozenset[ReasoningSessionState]]
] = MappingProxyType(
    {
        ReasoningSessionState.CREATED: frozenset(
            {
                ReasoningSessionState.INITIALIZED,
                ReasoningSessionState.CANCELLED,
                ReasoningSessionState.FAILED,
            }
        ),
        ReasoningSessionState.INITIALIZED: frozenset(
            {
                ReasoningSessionState.COLLECTING_EVIDENCE,
                ReasoningSessionState.CANCELLED,
                ReasoningSessionState.FAILED,
            }
        ),
        ReasoningSessionState.COLLECTING_EVIDENCE: frozenset(
            {
                ReasoningSessionState.REASONING,
                ReasoningSessionState.CANCELLED,
                ReasoningSessionState.FAILED,
            }
        ),
        ReasoningSessionState.REASONING: frozenset(
            {
                ReasoningSessionState.REVIEW,
                ReasoningSessionState.CANCELLED,
                ReasoningSessionState.FAILED,
            }
        ),
        ReasoningSessionState.REVIEW: frozenset(
            {
                ReasoningSessionState.COMPLETED,
                ReasoningSessionState.COLLECTING_EVIDENCE,
                ReasoningSessionState.REASONING,
                ReasoningSessionState.CANCELLED,
                ReasoningSessionState.FAILED,
            }
        ),
        ReasoningSessionState.COMPLETED: frozenset(),
        ReasoningSessionState.CANCELLED: frozenset(),
        ReasoningSessionState.FAILED: frozenset(),
    }
)

TERMINAL_STATES: Final[frozenset[ReasoningSessionState]] = frozenset(
    {
        ReasoningSessionState.COMPLETED,
        ReasoningSessionState.CANCELLED,
        ReasoningSessionState.FAILED,
    }
)


class ReasoningSessionLifecycle:
    """Validate and apply immutable reasoning-session transitions."""

    transition_map = TRANSITION_MAP
    terminal_states = TERMINAL_STATES

    @classmethod
    def allowed_targets(
        cls,
        source_state: ReasoningSessionState,
    ) -> tuple[ReasoningSessionState, ...]:
        cls._validate_state(source_state)
        return tuple(
            sorted(
                cls.transition_map[source_state],
                key=lambda state: state.value,
            )
        )

    @classmethod
    def can_transition(
        cls,
        source_state: ReasoningSessionState,
        target_state: ReasoningSessionState,
    ) -> bool:
        cls._validate_state(source_state)
        cls._validate_state(target_state)
        return target_state in cls.transition_map[source_state]

    @classmethod
    def is_terminal(cls, state: ReasoningSessionState) -> bool:
        cls._validate_state(state)
        return state in cls.terminal_states

    @classmethod
    def transition(
        cls,
        session: ReasoningSession,
        target_state: ReasoningSessionState,
    ) -> ReasoningSession:
        cls._validate_session(session)
        cls._validate_state(target_state)

        source_state = session.state

        if source_state in cls.terminal_states:
            raise TerminalReasoningSessionError(
                "Reasoning session is terminal and cannot transition: "
                f"{source_state.value} -> {target_state.value}"
            )

        if target_state == source_state:
            raise InvalidReasoningSessionTransitionError(
                "Reasoning session cannot transition to its current state: "
                f"{source_state.value}"
            )

        if target_state not in cls.transition_map[source_state]:
            raise InvalidReasoningSessionTransitionError(
                "Illegal reasoning-session transition: "
                f"{source_state.value} -> {target_state.value}"
            )

        successor = replace(
            session,
            state=target_state,
            revision=session.revision + 1,
        )

        cls._validate_successor(
            previous=session,
            successor=successor,
            target_state=target_state,
        )
        return successor

    @classmethod
    def _validate_state(cls, state: ReasoningSessionState) -> None:
        if not isinstance(state, ReasoningSessionState):
            raise ReasoningSessionContractError(
                "Lifecycle state must be a ReasoningSessionState"
            )

        if state not in cls.transition_map:
            raise ReasoningSessionContractError(
                f"Lifecycle state is not governed: {state.value}"
            )

    @classmethod
    def _validate_session(cls, session: ReasoningSession) -> None:
        if not isinstance(session, ReasoningSession):
            raise ReasoningSessionContractError(
                "Lifecycle requires a ReasoningSession"
            )

        if not is_dataclass(session):
            raise ReasoningSessionContractError(
                "ReasoningSession must remain a dataclass contract"
            )

        cls._validate_state(session.state)

        if isinstance(session.revision, bool) or not isinstance(
            session.revision,
            int,
        ):
            raise ReasoningSessionContractError(
                "ReasoningSession revision must be an integer"
            )

        if session.revision < 0:
            raise ReasoningSessionContractError(
                "ReasoningSession revision must be non-negative"
            )

    @classmethod
    def _validate_successor(
        cls,
        *,
        previous: ReasoningSession,
        successor: ReasoningSession,
        target_state: ReasoningSessionState,
    ) -> None:
        if successor is previous:
            raise ReasoningSessionContractError(
                "Lifecycle transition must create a new session snapshot"
            )

        if successor.state is not target_state:
            raise ReasoningSessionContractError(
                "Successor state does not match requested target state"
            )

        if successor.revision != previous.revision + 1:
            raise ReasoningSessionContractError(
                "Successor revision must increment by exactly one"
            )

        for contract_field in fields(previous):
            if contract_field.name in {"state", "revision"}:
                continue

            if getattr(successor, contract_field.name) != getattr(
                previous,
                contract_field.name,
            ):
                raise ReasoningSessionContractError(
                    "Lifecycle transition changed protected field: "
                    f"{contract_field.name}"
                )


LifecycleManager = ReasoningSessionLifecycle


__all__ = [
    "LifecycleManager",
    "ReasoningSessionLifecycle",
    "TERMINAL_STATES",
    "TRANSITION_MAP",
]
