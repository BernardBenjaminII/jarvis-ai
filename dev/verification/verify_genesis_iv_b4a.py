"""Certification verifier for Genesis IV-B4A."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.observation as observation_api  # noqa: E402
from core.observation.audit import (  # noqa: E402
    audit_observation_definitions,
)
from core.observation.migration_registry import (  # noqa: E402
    migration_registry_fingerprint,
)


REQUIRED_FILES = (
    "core/observation/__init__.py",
    "core/observation/adapters.py",
    "tests/test_genesis_iv_b4a_certification_repair.py",
    "dev/verification/verify_genesis_iv_b4a.py",
    "dev/verify_genesis_4b4a.sh",
)

STABLE_EXPORTS = (
    "Observation",
    "adapt_cognition_observation",
    "adapt_executive_observation",
    "adapt_legacy_observation",
)

MIGRATION_EXPORTS = (
    "adapt_cognition_common_observation",
    "adapt_operational_observation",
    "adapt_registered_observation",
    "adapt_representation_observation",
    "canonicalize_observation",
    "migration_registry_fingerprint",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B4A file set",
    )
    check(
        all(hasattr(observation_api, name) for name in STABLE_EXPORTS),
        "Stable IV-B3 public adapter imports restored",
    )
    check(
        all(name in observation_api.__all__ for name in STABLE_EXPORTS),
        "Stable IV-B3 exports declared",
    )
    check(
        all(hasattr(observation_api, name) for name in MIGRATION_EXPORTS),
        "IV-B4 migration public imports preserved",
    )

    report = audit_observation_definitions(ROOT)
    check(
        not report.forbidden_duplicates,
        "No ungoverned Observation definitions",
    )
    check(
        report.canonical_definitions
        == ("core/observation/contracts.py",),
        "Exactly one canonical Observation owner",
    )

    fingerprint = migration_registry_fingerprint()
    check(
        len(fingerprint) == 64,
        "Deterministic migration registry fingerprint",
    )
    print(f"[PASS] Migration registry fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()
