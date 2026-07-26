from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from core.integration.contracts import (
    ExecutiveProjection,
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)


class GenesisVIB0IntegrationContractConvergenceTests(unittest.TestCase):
    def _health(self) -> ProjectionHealth:
        return ProjectionHealth(
            status=ProjectionStatus.AVAILABLE,
            summary="Projection is available.",
            details={"count": 1},
        )

    def _envelope(self) -> ProjectionEnvelope:
        return ProjectionEnvelope(
            projection_id="capabilities",
            schema_version="1.1",
            generated_at=datetime.now(timezone.utc),
            source_timestamp=None,
            provider="tests.CapabilityProjectionProvider",
            health=self._health(),
            data={"total": 1},
        )

    def test_provider_contracts_are_public(self) -> None:
        import core.integration as integration

        for name in (
            "ProjectionEnvelope",
            "ProjectionHealth",
            "ProjectionStatus",
            "ExecutiveProjection",
        ):
            self.assertTrue(hasattr(integration, name), name)

    def test_projection_health_is_immutable(self) -> None:
        health = self._health()
        self.assertIsInstance(health.details, MappingProxyType)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            health.summary = "changed"  # type: ignore[misc]

    def test_projection_envelope_accepts_provider_shape(self) -> None:
        envelope = self._envelope()
        self.assertEqual(envelope.projection_id, "capabilities")
        self.assertTrue(envelope.available)
        self.assertIsInstance(envelope.data, MappingProxyType)

    def test_naive_generated_time_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            ProjectionEnvelope(
                projection_id="capabilities",
                schema_version="1.1",
                generated_at=datetime.now(),
                source_timestamp=None,
                provider="tests.Provider",
                health=self._health(),
                data={},
            )

    def test_executive_projection_aggregates_envelopes(self) -> None:
        envelope = self._envelope()
        aggregate = ExecutiveProjection(
            generated_at=datetime.now(timezone.utc),
            projections=(envelope,),
            overall_status=ProjectionStatus.AVAILABLE,
        )
        self.assertEqual(aggregate.projections, (envelope,))

    def test_capability_provider_imports(self) -> None:
        from core.integration.providers.capabilities import (
            CapabilityProjectionProvider,
        )

        self.assertEqual(
            CapabilityProjectionProvider.projection_id,
            "capabilities",
        )


if __name__ == "__main__":
    unittest.main()
