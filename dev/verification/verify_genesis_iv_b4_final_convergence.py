"""Certification for final Genesis IV-B4 Observation convergence."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.observation as public_api
from core.observation.audit import (
    audit_observation_definitions,
    require_observation_convergence,
)
from core.observation.migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MIGRATION_ENTRIES,
    OBSERVATION_MIGRATION_REGISTRY,
    migration_entry_for_path,
    migration_registry_fingerprint,
)


REQUIRED_FILES = (
    "core/observation/migration_registry.py",
    "core/observation/audit.py",
    "core/observation/__init__.py",
    "tests/test_genesis_iv_b4_final_canonical_convergence.py",
    "dev/verification/verify_genesis_iv_b4_final_convergence.py",
    "dev/verify_genesis_4b4_final_convergence.sh",
    "docs/architecture/convergence/"
    "genesis_iv_b4_final_canonical_convergence.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def direct_observation_definitions() -> set[str]:
    definitions: set[str] = set()

    for path in sorted((ROOT / "core").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ),
                filename=str(path),
            )
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        if any(
            isinstance(node, ast.ClassDef)
            and node.name == "Observation"
            for node in tree.body
        ):
            definitions.add(
                path.relative_to(ROOT).as_posix()
            )

    return definitions


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical final-convergence file set",
    )

    check(
        MIGRATION_ENTRIES is OBSERVATION_MIGRATION_REGISTRY,
        "Legacy and canonical registries share identity",
    )

    required_public_names = (
        "MIGRATION_ENTRIES",
        "MIGRATION_SCHEMA_VERSION",
        "migration_entry_for_path",
        "migration_registry_fingerprint",
        "OBSERVATION_MIGRATION_REGISTRY",
        "migration_entry_for",
    )
    check(
        all(hasattr(public_api, name) for name in required_public_names),
        "Historical and canonical public APIs",
    )

    check(
        migration_entry_for_path(
            "core/cognition/contracts.py"
        )
        is None,
        "Public re-export excluded from ownership",
    )

    registered = {entry.path for entry in MIGRATION_ENTRIES}
    direct = direct_observation_definitions()
    check(
        direct.issubset(registered),
        "Every direct Observation definition is governed",
    )

    report = audit_observation_definitions(ROOT)
    check(
        report.canonical_definitions
        == (CANONICAL_OBSERVATION_PATH,),
        "Exactly one canonical Observation owner",
    )
    check(
        not report.forbidden_duplicates,
        "No forbidden Observation definitions",
    )

    require_observation_convergence(ROOT)
    check(
        report.converged,
        "Observation convergence enforcement",
    )

    fingerprint = migration_registry_fingerprint()
    check(
        len(fingerprint) == 64,
        f"Deterministic registry fingerprint: {fingerprint}",
    )


if __name__ == "__main__":
    main()
