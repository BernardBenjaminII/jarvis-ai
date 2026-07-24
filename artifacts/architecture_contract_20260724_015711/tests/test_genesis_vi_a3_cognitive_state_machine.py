"""Tests for Genesis VI-A3 deterministic cognitive state machine."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from core.cognition import (
    CognitiveEventKind,
    CognitiveState,
    CognitiveStateMachine,
    InvalidStateTransitionError,
    StateTransition,
    TransitionPolicy,
)


class DeterministicClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(seconds=1)
        return value


class CognitiveStateMachineTests(unittest.TestCase):
    def test_initial_state_is_idle(self) -> None:
        machine = CognitiveStateMachine()
        self.assertIs(machine.current_state, CognitiveState.IDLE)
        self.assertEqual(machine.transition_count, 0)
        self.assertFalse(machine.is_terminal)

    def test_canonical_transition_records_history_and_event(self) -> None:
        clock = DeterministicClock()
        machine = CognitiveStateMachine(clock=clock)

        transition = machine.transition_to(
            CognitiveState.INITIALIZING,
            reason="Begin cognition cycle.",
        )

        self.assertEqual(transition.sequence, 1)
        self.assertIs(transition.previous_state, CognitiveState.IDLE)
        self.assertIs(transition.next_state, CognitiveState.INITIALIZING)
        self.assertIs(machine.current_state, CognitiveState.INITIALIZING)
        self.assertEqual(machine.event_count, 1)
        self.assertIs(
            machine.events()[0].kind,
            CognitiveEventKind.STATE_CHANGED,
        )
        self.assertEqual(
            machine.events()[0].occurred_at,
            transition.occurred_at,
        )

    def test_illegal_transition_is_rejected_without_mutation(self) -> None:
        machine = CognitiveStateMachine()

        with self.assertRaises(InvalidStateTransitionError):
            machine.transition_to(
                CognitiveState.EXECUTING,
                reason="Skip executive lifecycle.",
            )

        self.assertIs(machine.current_state, CognitiveState.IDLE)
        self.assertEqual(machine.transition_count, 0)
        self.assertEqual(machine.event_count, 0)

    def test_self_transition_is_rejected(self) -> None:
        machine = CognitiveStateMachine()

        with self.assertRaises(InvalidStateTransitionError):
            machine.transition_to(
                CognitiveState.IDLE,
                reason="Remain idle.",
            )

    def test_guard_can_reject_otherwise_legal_transition(self) -> None:
        machine = CognitiveStateMachine()
        machine.transition_to(
            CognitiveState.INITIALIZING,
            reason="Initialize.",
        )

        with self.assertRaises(InvalidStateTransitionError):
            machine.transition_to(
                CognitiveState.OBSERVING,
                reason="Observe.",
                guard=lambda _previous, _next: False,
            )

        self.assertIs(machine.current_state, CognitiveState.INITIALIZING)
        self.assertEqual(machine.transition_count, 1)

    def test_complete_canonical_path(self) -> None:
        machine = CognitiveStateMachine(clock=DeterministicClock())
        path = (
            CognitiveState.INITIALIZING,
            CognitiveState.OBSERVING,
            CognitiveState.ATTENDING,
            CognitiveState.RETRIEVING,
            CognitiveState.REASONING,
            CognitiveState.EVALUATING,
            CognitiveState.PLANNING,
            CognitiveState.EXECUTING,
            CognitiveState.REFLECTING,
            CognitiveState.COMPLETED,
        )

        transitions = machine.transition_path(
            path,
            reason_prefix="Canonical lifecycle",
        )

        self.assertEqual(len(transitions), len(path))
        self.assertIs(machine.current_state, CognitiveState.COMPLETED)
        self.assertTrue(machine.is_terminal)

    def test_completed_state_has_no_outbound_transition(self) -> None:
        policy = CognitiveStateMachine().policy
        self.assertEqual(policy.allowed_from(CognitiveState.COMPLETED), ())

    def test_failure_recovery_path(self) -> None:
        machine = CognitiveStateMachine()
        machine.transition_path(
            (
                CognitiveState.INITIALIZING,
                CognitiveState.OBSERVING,
                CognitiveState.FAILED,
                CognitiveState.REFLECTING,
                CognitiveState.COMPLETED,
            ),
            reason_prefix="Failure recovery",
        )
        self.assertIs(machine.current_state, CognitiveState.COMPLETED)

    def test_suspension_can_resume_at_controlled_state(self) -> None:
        machine = CognitiveStateMachine()
        machine.transition_path(
            (
                CognitiveState.INITIALIZING,
                CognitiveState.OBSERVING,
                CognitiveState.ATTENDING,
                CognitiveState.SUSPENDED,
                CognitiveState.ATTENDING,
                CognitiveState.REASONING,
            ),
            reason_prefix="Suspend and resume",
        )
        self.assertIs(machine.current_state, CognitiveState.REASONING)

    def test_snapshot_is_detached_and_immutable(self) -> None:
        machine = CognitiveStateMachine()
        machine.transition_to(
            CognitiveState.INITIALIZING,
            reason="Initialize.",
        )
        snapshot = machine.snapshot()

        machine.transition_to(
            CognitiveState.OBSERVING,
            reason="Observe.",
        )

        self.assertIs(
            snapshot.current_state,
            CognitiveState.INITIALIZING,
        )
        self.assertEqual(snapshot.transition_count, 1)
        self.assertEqual(snapshot.event_count, 1)

    def test_replay_reconstructs_state_and_history(self) -> None:
        original = CognitiveStateMachine(clock=DeterministicClock())
        original.transition_path(
            (
                CognitiveState.INITIALIZING,
                CognitiveState.OBSERVING,
                CognitiveState.ATTENDING,
                CognitiveState.REASONING,
                CognitiveState.EVALUATING,
                CognitiveState.PLANNING,
            ),
            reason_prefix="Replay source",
        )

        replayed = CognitiveStateMachine.replay(
            original.transitions(),
            clock=DeterministicClock(),
        )

        self.assertIs(replayed.current_state, original.current_state)
        self.assertEqual(replayed.transitions(), original.transitions())
        self.assertEqual(replayed.event_count, original.transition_count)
        self.assertTrue(
            all(event.metadata["replayed"] for event in replayed.events())
        )

    def test_replay_rejects_sequence_gap(self) -> None:
        transition = StateTransition(
            sequence=2,
            previous_state=CognitiveState.IDLE,
            next_state=CognitiveState.INITIALIZING,
            reason="Invalid sequence.",
        )

        with self.assertRaises(InvalidStateTransitionError):
            CognitiveStateMachine.replay((transition,))

    def test_custom_policy_is_supported(self) -> None:
        policy = TransitionPolicy(
            transitions={
                CognitiveState.IDLE: (CognitiveState.COMPLETED,),
                CognitiveState.COMPLETED: (),
            }
        )
        machine = CognitiveStateMachine(policy=policy)
        machine.transition_to(
            CognitiveState.COMPLETED,
            reason="Custom terminal path.",
        )
        self.assertTrue(machine.is_terminal)


if __name__ == "__main__":
    unittest.main()
