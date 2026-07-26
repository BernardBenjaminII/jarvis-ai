"""Genesis IV-B4A public API compatibility repair tests."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

import core.observation as observation_api
from core.observation.adapters import (
    adapt_cognition_observation,
    adapt_executive_observation,
    adapt_legacy_observation,
)


STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


class GenesisIVB4ACertificationRepairTests(unittest.TestCase):
    def test_stable_adapter_exports_are_importable(self) -> None:
        for name in (
            "adapt_cognition_observation",
            "adapt_executive_observation",
            "adapt_legacy_observation",
        ):
            self.assertTrue(hasattr(observation_api, name))
            self.assertIn(name, observation_api.__all__)

    def test_new_migration_exports_remain_available(self) -> None:
        for name in (
            "adapt_cognition_common_observation",
            "adapt_operational_observation",
            "adapt_representation_observation",
            "canonicalize_observation",
            "migration_registry_fingerprint",
        ):
            self.assertTrue(hasattr(observation_api, name))
            self.assertIn(name, observation_api.__all__)

    def test_cognition_compatibility_facade(self) -> None:
        legacy = SimpleNamespace(
            observation_id="legacy-cognition",
            subject="document",
            predicate="contains",
            value={"claim": "knowledge"},
            source=SimpleNamespace(identifier="legacy:book"),
            confidence=0.9,
            observed_at=STAMP,
            recorded_at=STAMP,
        )
        first = adapt_cognition_observation(legacy)
        second = observation_api.adapt_cognition_common_observation(
            legacy
        )
        self.assertEqual(first.observation_id, second.observation_id)

    def test_executive_compatibility_facade(self) -> None:
        legacy = SimpleNamespace(
            observation_id="legacy-runtime",
            observation_type="runtime.health",
            value={"healthy": True},
            provenance=SimpleNamespace(identifier="runtime:test"),
            occurred_at=STAMP,
            recorded_at=STAMP,
            confidence=1.0,
            mission_id="mission-1",
        )
        first = adapt_executive_observation(legacy)
        second = observation_api.adapt_operational_observation(legacy)
        self.assertEqual(first.observation_id, second.observation_id)

    def test_keyword_style_compatibility_call(self) -> None:
        canonical = adapt_legacy_observation(
            statement="A represented statement.",
            confidence=0.8,
            observed_at=STAMP,
            recorded_at=STAMP,
        )
        self.assertEqual(canonical.value, "A represented statement.")


if __name__ == "__main__":
    unittest.main()
