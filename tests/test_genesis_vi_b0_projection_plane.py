from __future__ import annotations

import unittest
from datetime import datetime, timezone

from core.integration.contracts import (
    ExecutiveProjection,
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)
from core.integration.errors import (
    DuplicateProjectionProviderError,
    ProjectionProviderNotFoundError,
)
from core.integration.registry import ProjectionRegistry
from core.integration.service import ExecutiveProjectionService


class FixtureProvider:
    projection_id = "fixture"
    schema_version = "1.0"

    def project(self) -> ProjectionEnvelope:
        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=datetime.now(timezone.utc),
            source_timestamp=None,
            provider=f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            health=ProjectionHealth(
                status=ProjectionStatus.AVAILABLE,
                summary="Fixture projection available.",
            ),
            data={"value": 1},
        )


class BrokenProvider:
    projection_id = "broken"
    schema_version = "1.0"

    def project(self) -> ProjectionEnvelope:
        raise RuntimeError("fixture failure")


class GenesisVIB0ProjectionPlaneTests(unittest.TestCase):
    def test_projection_registry_registers_and_gets(self) -> None:
        registry = ProjectionRegistry()
        provider = FixtureProvider()
        self.assertIs(registry.register(provider), provider)
        self.assertIs(registry.get("fixture"), provider)

    def test_projection_registry_rejects_duplicates(self) -> None:
        registry = ProjectionRegistry((FixtureProvider(),))
        with self.assertRaises(DuplicateProjectionProviderError):
            registry.register(FixtureProvider())

    def test_projection_registry_reports_missing_provider(self) -> None:
        with self.assertRaises(ProjectionProviderNotFoundError):
            ProjectionRegistry().get("missing")

    def test_projection_envelopes_returns_typed_values(self) -> None:
        service = ExecutiveProjectionService(
            ProjectionRegistry((FixtureProvider(),))
        )
        result = service.projection_envelopes()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ProjectionEnvelope)

    def test_failed_provider_becomes_unavailable_envelope(self) -> None:
        service = ExecutiveProjectionService(
            ProjectionRegistry((BrokenProvider(),))
        )
        result = service.projection("broken")
        self.assertEqual(
            result.health.status,
            ProjectionStatus.UNAVAILABLE,
        )
        self.assertTrue(result.errors)

    def test_executive_projection_aggregates_providers(self) -> None:
        service = ExecutiveProjectionService(
            ProjectionRegistry((FixtureProvider(), BrokenProvider()))
        )
        result = service.executive_projection()
        self.assertIsInstance(result, ExecutiveProjection)
        self.assertEqual(
            result.overall_status,
            ProjectionStatus.UNAVAILABLE,
        )

    def test_envelope_supports_provider_error_field(self) -> None:
        envelope = ProjectionEnvelope(
            projection_id="fixture",
            schema_version="1.0",
            generated_at=datetime.now(timezone.utc),
            source_timestamp=None,
            provider="tests.FixtureProvider",
            health=ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Partial result.",
            ),
            data={},
            errors=("one failure",),
        )
        self.assertEqual(envelope.errors, ("one failure",))

    def test_unknown_status_is_supported(self) -> None:
        health = ProjectionHealth(
            status=ProjectionStatus.UNKNOWN,
            summary="State cannot be determined.",
        )
        self.assertEqual(health.status.value, "unknown")


if __name__ == "__main__":
    unittest.main()
