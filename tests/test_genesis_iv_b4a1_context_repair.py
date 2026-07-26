"""Genesis IV-B4A.1 ObservationContext construction repair tests."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from core.observation.adapters import (
    adapt_cognition_observation,
    adapt_executive_observation,
    adapt_legacy_observation,
)
from core.observation.contracts import ObservationContext
from core.observation.migration import _make_context

STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


class GenesisIVB4A1ContextRepairTests(unittest.TestCase):
    def test_context_constructs_against_actual_contract(self) -> None:
        context = _make_context(
            {
                "legacy_contract": "test",
                "mission_id": "mission-1",
            }
        )
        self.assertIsInstance(context, ObservationContext)

    def test_cognition_adapter_constructs_context(self) -> None:
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
        canonical = adapt_cognition_observation(legacy)
        self.assertIsInstance(canonical.context, ObservationContext)

    def test_operational_adapter_constructs_context(self) -> None:
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
        canonical = adapt_executive_observation(legacy)
        self.assertIsInstance(canonical.context, ObservationContext)

    def test_representation_adapter_constructs_context(self) -> None:
        canonical = adapt_legacy_observation(
            statement="A represented statement.",
            confidence=0.8,
            observed_at=STAMP,
            recorded_at=STAMP,
        )
        self.assertIsInstance(canonical.context, ObservationContext)


if __name__ == "__main__":
    unittest.main()
