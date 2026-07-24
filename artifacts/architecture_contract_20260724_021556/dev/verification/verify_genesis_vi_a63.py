#!/usr/bin/env python3
"""Structural and deterministic verification for Genesis VI-A6.3."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.executive.persistence import FileCheckpointRepository  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    expected_files = (
        ROOT / "core/executive/persistence/storage.py",
        ROOT / "core/executive/persistence/checkpoint.py",
        ROOT / "core/executive/persistence/repository.py",
        ROOT / "docs/architecture/genesis_vi_a63_executive_checkpoint_store.md",
        ROOT / "tests/test_genesis_vi_a63_checkpoint_store.py",
    )
    require(all(path.is_file() for path in expected_files), "required files missing")
    print("[PASS] Canonical VI-A6.3 file structure")

    with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
        arguments = dict(
            session_id="certification-session",
            mission_id="certification-mission",
            payload=b'{"executive":"stable","phase":"VI-A6.3"}',
            schema_name="jarvis.executive.snapshot",
            schema_version=1,
            created_at=datetime(2026, 7, 22, 20, 0, tzinfo=timezone.utc),
            metadata={"reason": "certification"},
        )
        first_repository = FileCheckpointRepository(left)
        second_repository = FileCheckpointRepository(right)
        first = first_repository.save(**arguments)
        second = second_repository.save(**arguments)

        require(
            first.checkpoint_sha256 == second.checkpoint_sha256,
            "checkpoint digest is not deterministic",
        )
        require(
            first.payload_sha256 == second.payload_sha256,
            "payload digest is not deterministic",
        )
        print("[PASS] Deterministic checkpoint construction")

        loaded = first_repository.load("certification-session", 1)
        require(loaded == first, "checkpoint round trip changed record")
        print("[PASS] Immutable checkpoint round trip")

        summary = first_repository.verify("certification-session", 1)
        require(summary.sequence == 1, "verification summary invalid")
        print("[PASS] Repository integrity verification")

        fingerprint_material = "\n".join(
            [
                first.checkpoint_id,
                first.checkpoint_sha256,
                first.payload_sha256,
                first.parent_checkpoint_sha256,
                first.schema_name,
                str(first.schema_version),
            ]
        ).encode("utf-8")
        fingerprint = hashlib.sha256(fingerprint_material).hexdigest()
        print(f"[PASS] Architecture fingerprint: {fingerprint}")

    source = (ROOT / "core/executive/persistence/repository.py").read_text(
        encoding="utf-8"
    )
    forbidden = ("sqlite3", "sqlalchemy", "requests", "httpx")
    require(
        not any(token in source for token in forbidden),
        "repository introduced a forbidden external persistence dependency",
    )
    print("[PASS] Database-free repository boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
