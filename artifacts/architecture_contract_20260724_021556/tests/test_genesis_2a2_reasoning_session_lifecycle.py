"""Tests for Genesis II-A2 immutable reasoning-session lifecycle."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from core.reasoning.session import (
    InvalidReasoningSessionTransitionError,
    ReasoningSessionLifecycle,
    ReasoningSessionState,
    TERMINAL_STATES,
    TRANSITION_MAP,
    TerminalReasoningSessionError,
)
from tests.fixtures.reasoning import make_reasoning_session


def test_transition_map_is_immutable() -> None:
    assert isinstance(TRANSITION_MAP, MappingProxyType)

    with pytest.raises(TypeError):
        TRANSITION_MAP[ReasoningSessionState.CREATED] = frozenset()  # type: ignore[index]


def test_transition_map_governs_every_state() -> None:
    assert set(TRANSITION_MAP) == set(ReasoningSessionState)


def test_terminal_states_have_no_successors() -> None:
    assert TERMINAL_STATES == {
        ReasoningSessionState.COMPLETED,
        ReasoningSessionState.CANCELLED,
        ReasoningSessionState.FAILED,
    }

    for state in TERMINAL_STATES:
        assert TRANSITION_MAP[state] == frozenset()


@pytest.mark.parametrize(
    ("source", "target"),
    (
        (ReasoningSessionState.CREATED, ReasoningSessionState.INITIALIZED),
        (
            ReasoningSessionState.INITIALIZED,
            ReasoningSessionState.COLLECTING_EVIDENCE,
        ),
        (
            ReasoningSessionState.COLLECTING_EVIDENCE,
            ReasoningSessionState.REASONING,
        ),
        (ReasoningSessionState.REASONING, ReasoningSessionState.REVIEW),
        (ReasoningSessionState.REVIEW, ReasoningSessionState.COMPLETED),
        (
            ReasoningSessionState.REVIEW,
            ReasoningSessionState.COLLECTING_EVIDENCE,
        ),
        (ReasoningSessionState.REVIEW, ReasoningSessionState.REASONING),
    ),
)
def test_declared_transitions_are_legal(
    source: ReasoningSessionState,
    target: ReasoningSessionState,
) -> None:
    assert ReasoningSessionLifecycle.can_transition(source, target)


def test_first_transition_advances_revision_zero_to_one() -> None:
    session = make_reasoning_session()

    successor = ReasoningSessionLifecycle.transition(
        session,
        ReasoningSessionState.INITIALIZED,
    )

    assert session.revision == 0
    assert successor.revision == 1


def test_transition_returns_new_immutable_snapshot() -> None:
    session = make_reasoning_session()

    successor = ReasoningSessionLifecycle.transition(
        session,
        ReasoningSessionState.INITIALIZED,
    )

    assert successor is not session
    assert session.state is ReasoningSessionState.CREATED
    assert successor.state is ReasoningSessionState.INITIALIZED
    assert successor.revision == session.revision + 1

    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        successor.state = ReasoningSessionState.REASONING  # type: ignore[misc]


def test_transition_preserves_protected_fields() -> None:
    session = make_reasoning_session()

    successor = ReasoningSessionLifecycle.transition(
        session,
        ReasoningSessionState.INITIALIZED,
    )

    for item in fields(session):
        if item.name not in {"state", "revision"}:
            assert getattr(successor, item.name) == getattr(
                session,
                item.name,
            )


def test_equivalent_transitions_are_deterministic() -> None:
    session = make_reasoning_session()

    first = ReasoningSessionLifecycle.transition(
        session,
        ReasoningSessionState.INITIALIZED,
    )
    second = ReasoningSessionLifecycle.transition(
        session,
        ReasoningSessionState.INITIALIZED,
    )

    assert first == second


def test_illegal_transition_is_rejected() -> None:
    session = make_reasoning_session()

    with pytest.raises(InvalidReasoningSessionTransitionError):
        ReasoningSessionLifecycle.transition(
            session,
            ReasoningSessionState.REASONING,
        )


@pytest.mark.parametrize("state", tuple(TERMINAL_STATES))
def test_terminal_sessions_cannot_transition(
    state: ReasoningSessionState,
) -> None:
    session = make_reasoning_session(state=state)

    with pytest.raises(TerminalReasoningSessionError):
        ReasoningSessionLifecycle.transition(
            session,
            ReasoningSessionState.CREATED,
        )


def test_same_state_transition_is_rejected() -> None:
    session = make_reasoning_session()

    with pytest.raises(InvalidReasoningSessionTransitionError):
        ReasoningSessionLifecycle.transition(
            session,
            ReasoningSessionState.CREATED,
        )


def test_allowed_targets_are_deterministically_ordered() -> None:
    targets = ReasoningSessionLifecycle.allowed_targets(
        ReasoningSessionState.REVIEW
    )

    assert targets == tuple(
        sorted(targets, key=lambda state: state.value)
    )
