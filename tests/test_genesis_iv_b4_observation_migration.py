"""Genesis IV-B4 migration and compatibility tests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import unittest
import warnings

from core.observation.audit import audit_observation_definitions
from core.observation.compatibility import (
    LegacyObservationCompatibilityWarning,
    canonicalize_observation,
)
from core.observation.migration import (
    adapt_cognition_common_observation,
    adapt_operational_observation,
    adapt_representation_observation,
)
from core.observation.migration_registry import (
    MIGRATION_ENTRIES,
    migration_registry_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


class MigrationTests(unittest.TestCase):
    def test_registry_covers_discovered_noncanonical_definitions(self) -> None:
        report = audit_observation_definitions(ROOT)
        discovered = {
            item.path
            for item in report.definitions
            if not item.canonical
        }
        registered = {entry.path for entry in MIGRATION_ENTRIES}
        self.assertEqual(discovered, registered)
        self.assertFalse(report.forbidden_duplicates)

    def test_registry_fingerprint_is_deterministic(self) -> None:
        self.assertEqual(
            migration_registry_fingerprint(),
            migration_registry_fingerprint(),
        )

    def test_cognition_common_adapter_is_deterministic(self) -> None:
        source = SimpleNamespace(identifier="legacy:book")
        legacy = SimpleNamespace(
            observation_id="legacy-1",
            subject="document",
            predicate="contains",
            value={"claim": "knowledge"},
            source=source,
            confidence=Decimal("0.9"),
            observed_at=STAMP,
            recorded_at=STAMP,
            origin="direct_extraction",
            polarity="affirmed",
        )
        first = adapt_cognition_common_observation(legacy)
        second = adapt_cognition_common_observation(legacy)
        self.assertEqual(
            first.observation_id,
            second.observation_id,
        )

    def test_operational_adapter_preserves_time_and_context(self) -> None:
        provenance = SimpleNamespace(identifier="runtime:test")
        legacy = SimpleNamespace(
            observation_id="legacy-runtime",
            observation_type="runtime.health",
            value={"healthy": True},
            provenance=provenance,
            occurred_at=STAMP,
            recorded_at=STAMP,
            confidence=1.0,
            mission_id="mission-1",
            correlation_id="corr-1",
            severity="informational",
        )
        canonical = adapt_operational_observation(legacy)
        self.assertEqual(canonical.observed_at, STAMP)
        self.assertEqual(canonical.recorded_at, STAMP)

    def test_representation_adapter_preserves_statement(self) -> None:
        legacy = SimpleNamespace(
            statement="The source makes a bounded claim.",
            confidence=0.75,
            observed_at=STAMP,
            recorded_at=STAMP,
            object_id="representation-1",
        )
        canonical = adapt_representation_observation(legacy)
        self.assertEqual(
            canonical.value,
            "The source makes a bounded claim.",
        )

    def test_compatibility_boundary_emits_warning(self) -> None:
        legacy = SimpleNamespace(
            statement="Compatibility boundary test.",
            confidence=1.0,
            observed_at=STAMP,
            recorded_at=STAMP,
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter(
                "always",
                LegacyObservationCompatibilityWarning,
            )
            canonical, receipt = canonicalize_observation(
                legacy,
                legacy_path="core/representation/contracts.py",
            )
        self.assertTrue(receipt.adapter_applied)
        self.assertEqual(
            receipt.canonical_observation_id,
            canonical.observation_id,
        )
        self.assertEqual(len(caught), 1)


if __name__ == "__main__":
    unittest.main()
