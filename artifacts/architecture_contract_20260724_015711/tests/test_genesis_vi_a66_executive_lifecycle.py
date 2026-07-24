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
