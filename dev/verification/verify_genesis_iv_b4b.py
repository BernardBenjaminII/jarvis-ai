from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.adapters import adapt_legacy_observation
from core.observation.audit import (
    ObservationDefinitionStatus,
    audit_observation_definitions,
)
from core.observation.enums import ObservationDomain


REQUIRED_FILES = (
    "tests/test_genesis_iv_b4b_behavioral_compatibility.py",
    "dev/verification/verify_genesis_iv_b4b.py",
    "dev/verify_genesis_4b4b.sh",
    "docs/architecture/convergence/"
    "genesis_iv_b4b_behavioral_compatibility.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B4B file set",
    )

    report = audit_observation_definitions(ROOT)
    definitions = {item.path: item for item in report.definitions}

    check(
        definitions["core/cognition/contracts.py"].status
        is ObservationDefinitionStatus.APPROVED_LEGACY,
        "Historical cognition contract approved",
    )
    check(
        not report.forbidden_duplicates,
        "No ungoverned Observation definitions",
    )

    stamp = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    legacy = SimpleNamespace(
        observation_id="legacy-runtime",
        observation_type="runtime.health",
        value={"healthy": True},
        provenance=SimpleNamespace(identifier="runtime:test"),
        occurred_at=stamp,
        recorded_at=stamp,
        confidence=1.0,
        mission_id="m1",
        correlation_id="c1",
    )
    canonical = adapt_legacy_observation(legacy)

    check(
        canonical.domain is ObservationDomain.PLATFORM,
        "Legacy PLATFORM domain preserved",
    )
    check(
        canonical.context.mission_id == "m1",
        "Legacy mission identifier preserved",
    )
    check(
        canonical.context.correlation_id == "c1",
        "Legacy correlation identifier preserved",
    )


if __name__ == "__main__":
    main()
