#!/usr/bin/env python3
"""Interactive demonstration of Genesis VI-A6.4."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Iterable

from core.executive.persistence import (
    ExecutiveIntegrityEngine,
    IntegrityPolicy,
    IntegrityReport,
)


SESSION_ID = "executive-session-demo"


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def digest(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DemoCheckpoint:
    checkpoint_id: str
    session_id: str
    sequence: int
    parent_digest: str | None
    schema: str
    payload: dict[str, object]
    payload_digest: str
    checkpoint_digest: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "parent_digest": self.parent_digest,
            "schema": self.schema,
            "payload": self.payload,
            "payload_digest": self.payload_digest,
            "checkpoint_digest": self.checkpoint_digest,
        }


class DemoRepository:
    """Minimal repository boundary consumed by the Integrity Engine."""

    def __init__(self, checkpoints: Iterable[DemoCheckpoint]) -> None:
        self._checkpoints = tuple(checkpoints)

    def history(self, session_id: str) -> tuple[DemoCheckpoint, ...]:
        return tuple(
            checkpoint
            for checkpoint in self._checkpoints
            if checkpoint.session_id == session_id
        )


def make_checkpoint(
    sequence: int,
    *,
    parent_digest: str | None,
    schema: str = "executive-state-v1",
    payload: dict[str, object] | None = None,
) -> DemoCheckpoint:
    state = payload or {
        "mission": "Demonstrate executive integrity",
        "sequence": sequence,
        "status": "active",
    }

    checkpoint_material = {
        "checkpoint_id": f"checkpoint-{sequence:04d}",
        "session_id": SESSION_ID,
        "sequence": sequence,
        "parent_digest": parent_digest,
        "schema": schema,
        "payload": state,
        "payload_digest": digest(state),
    }

    return DemoCheckpoint(
        **checkpoint_material,
        checkpoint_digest=digest(checkpoint_material),
    )


def build_valid_chain() -> tuple[DemoCheckpoint, ...]:
    checkpoints: list[DemoCheckpoint] = []
    parent_digest: str | None = None

    for sequence in range(1, 4):
        checkpoint = make_checkpoint(
            sequence,
            parent_digest=parent_digest,
        )
        checkpoints.append(checkpoint)
        parent_digest = checkpoint.checkpoint_digest

    return tuple(checkpoints)


def print_report(title: str, report: IntegrityReport) -> None:
    width = 78

    print()
    print("=" * width)
    print(title)
    print("=" * width)
    print(f"Session                 : {report.session_id}")
    print(f"Checkpoints examined    : {report.checkpoints_examined}")
    print(f"Certified               : {'YES' if report.certified else 'NO'}")
    print(f"Disposition             : {report.disposition.value.upper()}")
    print(f"Findings                : {len(report.findings)}")
    print(f"Repository fingerprint  : {report.repository_fingerprint}")
    print(f"Report fingerprint      : {report.report_fingerprint}")
    print(
        "Report fingerprint valid: "
        f"{'YES' if report.verify_fingerprint() else 'NO'}"
    )

    if not report.findings:
        print()
        print("[CERTIFIED] No integrity violations were detected.")
        return

    print()
    print("Integrity findings:")

    for number, finding in enumerate(report.findings, start=1):
        observation = finding.observation

        print()
        print(f"  Finding {number}")
        print(f"    Code        : {observation.code.value}")
        print(f"    Severity    : {finding.severity.value}")
        print(f"    Disposition : {finding.disposition.value}")
        print(f"    Checkpoint  : {observation.checkpoint_id or '-'}")
        print(f"    Sequence    : {observation.sequence or '-'}")

        if observation.expected is not None:
            print(f"    Expected    : {observation.expected}")

        if observation.actual is not None:
            print(f"    Actual      : {observation.actual}")

        print(f"    Detail      : {observation.detail}")


def run_scenario(
    title: str,
    checkpoints: Iterable[DemoCheckpoint],
    *,
    policy: IntegrityPolicy | None = None,
) -> None:
    repository = DemoRepository(checkpoints)
    engine = ExecutiveIntegrityEngine(repository, policy=policy)
    report = engine.verify_session(SESSION_ID)
    print_report(title, report)


def main() -> int:
    valid_chain = build_valid_chain()

    run_scenario(
        "SCENARIO 1 — VALID CERTIFIED CHECKPOINT CHAIN",
        valid_chain,
    )

    payload_tampered = list(valid_chain)
    payload_tampered[1] = replace(
        payload_tampered[1],
        payload={
            "mission": "Unauthorized altered mission",
            "sequence": 2,
            "status": "compromised",
        },
    )

    run_scenario(
        "SCENARIO 2 — PAYLOAD TAMPERING",
        payload_tampered,
    )

    sequence_gap = (
        valid_chain[0],
        replace(valid_chain[2], sequence=3),
    )

    run_scenario(
        "SCENARIO 3 — MISSING CHECKPOINT SEQUENCE",
        sequence_gap,
    )

    broken_parent = list(valid_chain)
    broken_parent[1] = replace(
        broken_parent[1],
        parent_digest="invalid-parent-digest",
    )

    run_scenario(
        "SCENARIO 4 — BROKEN PARENT LINK",
        broken_parent,
    )

    schema_policy = IntegrityPolicy(
        supported_schemas=frozenset({"executive-state-v2"})
    )

    run_scenario(
        "SCENARIO 5 — UNSUPPORTED SCHEMA",
        valid_chain,
        policy=schema_policy,
    )

    print()
    print("=" * 78)
    print("GENESIS VI-A6.4 TEST DRIVE COMPLETE")
    print("=" * 78)
    print()
    print("Expected behavior:")
    print("  Scenario 1: CERTIFIED / TRUSTED")
    print("  Scenario 2: NOT CERTIFIED / QUARANTINE")
    print("  Scenario 3: NOT CERTIFIED / QUARANTINE")
    print("  Scenario 4: NOT CERTIFIED / QUARANTINE")
    print("  Scenario 5: NOT CERTIFIED / REQUIRES_MIGRATION")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
