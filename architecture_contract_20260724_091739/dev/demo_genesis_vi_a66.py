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
