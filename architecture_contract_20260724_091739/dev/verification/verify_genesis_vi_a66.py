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
