#!/usr/bin/env python3
"""Verify Genesis IV-R3A Pack 3 architecture reconciliation assets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ROOT / "docs" / "architecture" / "cognitive_ownership.md",
    ROOT / "docs" / "architecture" / "evidence_engine.md",
    ROOT / "dev" / "audit_cognitive_ownership.py",
    ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.md",
    ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json",
)

REQUIRED_OWNERSHIP_TEXT = (
    "Each cognitive concept has exactly one canonical owning subsystem.",
    "`core.evidence` is the canonical owner",
    "Controlled Migration Protocol",
    "do not:",
)

REQUIRED_EVIDENCE_TEXT = (
    "The Evidence Engine transforms validated observations",
    "Admissibility Evaluation",
    "Dependencies must not point from Evidence into Reasoning or Executive.",
    "Certification proves a pack",
)


def check(condition: bool, label: str) -> int:
    if condition:
        print(f"[PASS] {label}")
        return 0
    print(f"[FAIL] {label}")
    return 1


def main() -> int:
    failures = 0

    failures += check(
        all(path.is_file() for path in REQUIRED_FILES),
        "Required reconciliation assets",
    )

    ownership = (ROOT / "docs" / "architecture" / "cognitive_ownership.md").read_text(
        encoding="utf-8"
    )
    evidence = (ROOT / "docs" / "architecture" / "evidence_engine.md").read_text(
        encoding="utf-8"
    )

    failures += check(
        all(text in ownership for text in REQUIRED_OWNERSHIP_TEXT),
        "Canonical ownership invariants",
    )
    failures += check(
        all(text in evidence for text in REQUIRED_EVIDENCE_TEXT),
        "Evidence Engine specification invariants",
    )

    result = subprocess.run(
        [sys.executable, "dev/audit_cognitive_ownership.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check(result.returncode == 0, "Ownership audit execution")

    data = json.loads(
        (ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json").read_text(
            encoding="utf-8"
        )
    )

    failures += check(
        data.get("canonical_owner") == "core.evidence",
        "Canonical Evidence owner",
    )
    failures += check(
        data.get("legacy_package") == "core.reasoning.evidence",
        "Legacy Evidence package identified",
    )
    failures += check(
        data.get("migration_eligible_for_removal") is False,
        "Legacy removal remains blocked pending migration",
    )
    failures += check(
        not data.get("parse_errors"),
        "Production Python syntax health",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
