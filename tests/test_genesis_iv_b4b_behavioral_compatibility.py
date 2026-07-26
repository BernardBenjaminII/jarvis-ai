"""Genesis IV-B4B behavioral compatibility tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest

from core.observation.adapters import adapt_legacy_observation
from core.observation.audit import audit_observation_definitions
from core.observation.enums import ObservationDomain
from core.observation.export_audit import scan_observation_exports


ROOT = Path(__file__).resolve().parents[1]
STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


class GenesisIVB4BBehavioralCompatibilityTests(unittest.TestCase):
    def test_public_contract_is_export_not_definition(self) -> None:
        report = audit_observation_definitions(ROOT)
        definition_paths = {item.path for item in report.definitions}
        self.assertNotIn("core/cognition/contracts.py", definition_paths)

        export_paths = {
            item.path for item in scan_observation_exports(ROOT)
        }
        self.assertIn("core/cognition/contracts.py", export_paths)

    def test_legacy_operational_domain_remains_platform(self) -> None:
        legacy = SimpleNamespace(
            observation_id="legacy-runtime",
            observation_type="runtime.health",
            value={"healthy": True},
            provenance=SimpleNamespace(identifier="runtime:test"),
            occurred_at=STAMP,
            recorded_at=STAMP,
            confidence=1.0,
            mission_id="m1",
        )
        canonical = adapt_legacy_observation(legacy)
        self.assertEqual(canonical.domain, ObservationDomain.PLATFORM)

    def test_legacy_context_identifiers_are_preserved(self) -> None:
        legacy = SimpleNamespace(
            observation_id="legacy-runtime",
            observation_type="runtime.health",
            value={"healthy": True},
            provenance=SimpleNamespace(identifier="runtime:test"),
            occurred_at=STAMP,
            recorded_at=STAMP,
            confidence=1.0,
            mission_id="m1",
            correlation_id="c1",
        )
        canonical = adapt_legacy_observation(legacy)
        self.assertEqual(canonical.context.mission_id, "m1")
        self.assertEqual(canonical.context.correlation_id, "c1")

    def test_no_ungoverned_observation_definitions(self) -> None:
        report = audit_observation_definitions(ROOT)
        self.assertFalse(report.forbidden_duplicates)


if __name__ == "__main__":
    unittest.main()
