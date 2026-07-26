"""Certification verifier for Genesis IV-B4C."""

from __future__ import annotations

from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MigrationDisposition,
    approved_legacy_entries,
    canonical_observation_entry,
    deprecated_rename_entries,
    migration_entries,
    migration_entry_for,
    migration_registry_fingerprint,
)


REQUIRED_FILES = (
    "core/observation/migration_registry.py",
    "tests/test_genesis_iv_b4c_migration_registry_reconstruction.py",
    "dev/verification/verify_genesis_iv_b4c.py",
    "dev/verify_genesis_4b4c.sh",
    "docs/architecture/convergence/"
    "genesis_iv_b4c_registry_reconstruction.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def direct_observation_definitions() -> set[str]:
    paths: set[str] = set()
    for base_name in ("core",):
        base = ROOT / base_name
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                )
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue

            if any(
                isinstance(node, ast.ClassDef)
                and node.name == "Observation"
                for node in tree.body
            ):
                paths.add(path.relative_to(ROOT).as_posix())
    return paths


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B4C file set",
    )

    entries = migration_entries()
    check(
        len({entry.path for entry in entries}) == len(entries),
        "Unique registry paths",
    )

    canonical = canonical_observation_entry()
    check(
        canonical.path == CANONICAL_OBSERVATION_PATH,
        "Canonical Observation owner",
    )
    check(
        canonical.disposition is MigrationDisposition.CANONICAL,
        "Canonical disposition",
    )

    check(
        migration_entry_for("core/cognition/contracts.py") is None,
        "Public re-export excluded from migration ownership",
    )

    check(
        tuple(entry.path for entry in approved_legacy_entries())
        == ("core/cognition/common/contracts.py",),
        "Approved legacy definition",
    )

    check(
        {
            entry.path: entry.target_name
            for entry in deprecated_rename_entries()
        }
        == {
            "core/cognition/observation/models.py":
            "ObservationRecord",
            "core/representation/contracts.py":
            "RepresentedStatement",
        },
        "Deprecated semantic rename plan",
    )

    direct = direct_observation_definitions()
    registered = {entry.path for entry in entries}
    check(
        direct.issubset(registered),
        "All direct Observation definitions governed",
    )

    fingerprint = migration_registry_fingerprint()
    check(
        len(fingerprint) == 64,
        f"Deterministic registry fingerprint: {fingerprint}",
    )


if __name__ == "__main__":
    main()
