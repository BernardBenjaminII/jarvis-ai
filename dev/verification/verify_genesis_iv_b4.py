"""Certification verifier for Genesis IV-B4."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.audit import (  # noqa: E402
    audit_observation_definitions,
    format_observation_convergence_report,
)
from core.observation.compatibility import (  # noqa: E402
    canonicalize_observation,
)
from core.observation.migration import (  # noqa: E402
    adapt_cognition_common_observation,
    adapt_operational_observation,
    adapt_representation_observation,
)
from core.observation.migration_registry import (  # noqa: E402
    MIGRATION_ENTRIES,
    migration_registry_fingerprint,
)


REQUIRED_FILES = (
    "core/observation/migration.py",
    "core/observation/migration_registry.py",
    "core/observation/compatibility.py",
    "dev/report_genesis_iv_b4_migration.py",
    "dev/verification/verify_genesis_iv_b4.py",
    "dev/verify_genesis_4b4.sh",
    "tests/test_genesis_iv_b4_observation_migration.py",
    "docs/architecture/convergence/"
    "genesis_iv_b4_observation_migration.md",
    "docs/decisions/ADR-0039-observation-migration-strategy.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B4 file set",
    )

    report = audit_observation_definitions(ROOT)
    print()
    print(format_observation_convergence_report(report))
    print()

    registered = {entry.path for entry in MIGRATION_ENTRIES}
    discovered = {
        item.path for item in report.definitions if not item.canonical
    }
    check(
        discovered == registered,
        "Migration registry covers every non-canonical definition",
    )
    check(
        not report.forbidden_duplicates,
        "No ungoverned Observation definitions",
    )
    check(
        report.approved_legacy_definitions
        == ("core/cognition/common/contracts.py",),
        "Legacy cognition contract governed",
    )
    check(
        report.deprecated_definitions
        == (
            "core/cognition/observation/models.py",
            "core/representation/contracts.py",
        ),
        "Semantic rename candidates governed",
    )

    stamp = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)

    cognition = SimpleNamespace(
        observation_id="legacy-cognition",
        subject="source",
        predicate="states",
        value={"claim": "fact"},
        source=SimpleNamespace(identifier="legacy:source"),
        confidence=0.9,
        observed_at=stamp,
        recorded_at=stamp,
    )
    operational = SimpleNamespace(
        observation_id="legacy-operational",
        observation_type="runtime.health",
        value={"healthy": True},
        provenance=SimpleNamespace(identifier="runtime:test"),
        occurred_at=stamp,
        recorded_at=stamp,
        confidence=1.0,
        mission_id="mission-1",
    )
    representation = SimpleNamespace(
        statement="A source-grounded represented statement.",
        confidence=0.8,
        observed_at=stamp,
        recorded_at=stamp,
    )

    cognition_result = adapt_cognition_common_observation(cognition)
    operational_result = adapt_operational_observation(operational)
    representation_result = adapt_representation_observation(
        representation
    )

    check(
        cognition_result.observation_id
        == adapt_cognition_common_observation(cognition).observation_id,
        "Cognition adapter deterministic",
    )
    check(
        operational_result.observed_at == stamp,
        "Operational adapter preserves occurrence time",
    )
    check(
        representation_result.value
        == "A source-grounded represented statement.",
        "Representation adapter preserves statement",
    )

    canonical, receipt = canonicalize_observation(
        operational,
        legacy_path="core/cognition/observation/models.py",
        warn=False,
    )
    check(
        receipt.adapter_applied
        and canonical.observation_id
        == receipt.canonical_observation_id,
        "Explicit compatibility boundary",
    )

    fingerprint = migration_registry_fingerprint()
    check(
        len(fingerprint) == 64,
        "Deterministic migration registry fingerprint",
    )
    print(f"[PASS] Migration registry fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()
