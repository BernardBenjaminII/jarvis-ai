from __future__ import annotations

import unittest
from datetime import datetime, timezone

from core.integration.contracts import (
    ExecutiveProjection,
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)
from core.integration.registry import ProjectionRegistry
from core.integration.service import ExecutiveProjectionService


class AvailableProvider:
    projection_id = "available"
    schema_version = "1.0"

    def project(self) -> ProjectionEnvelope:
        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=datetime.now(timezone.utc),
            source_timestamp=None,
            provider="tests.AvailableProvider",
            health=ProjectionHealth(
                status=ProjectionStatus.AVAILABLE,
                summary="Available.",
            ),
            data={"ready": True},
        )


class DegradedProvider:
    projection_id = "degraded"
    schema_version = "1.0"

    def project(self) -> ProjectionEnvelope:
        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=datetime.now(timezone.utc),
            source_timestamp=None,
            provider="tests.DegradedProvider",
            health=ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Degraded.",
                warnings=("fixture warning",),
            ),
            data={"ready": True},
            warnings=("fixture warning",),
        )


class GenesisVIB0AProjectionCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ExecutiveProjectionService(
            ProjectionRegistry(
                (
                    AvailableProvider(),
                    DegradedProvider(),
                )
            )
        )

    def test_projection_envelopes_is_typed_api(self) -> None:
        result = self.service.projection_envelopes()
        self.assertIsInstance(result, tuple)
        self.assertEqual(
            [item.projection_id for item in result],
            ["available", "degraded"],
        )
        self.assertTrue(
            all(isinstance(item, ProjectionEnvelope) for item in result)
        )

    def test_executive_projection_is_typed_aggregate(self) -> None:
        result = self.service.executive_projection()
        self.assertIsInstance(result, ExecutiveProjection)
        self.assertEqual(
            result.overall_status,
            ProjectionStatus.DEGRADED,
        )

    def test_all_projections_restores_historical_dictionary(self) -> None:
        result = self.service.all_projections()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["provider_count"], 2)
        self.assertEqual(result["summary"]["available"], 1)
        self.assertEqual(result["summary"]["degraded"], 1)
        self.assertEqual(result["summary"]["unavailable"], 0)
        self.assertEqual(result["summary"]["not_configured"], 0)
        self.assertEqual(result["summary"]["unknown"], 0)
        self.assertEqual(result["overall_status"], "degraded")
        self.assertEqual(
            [item["projection_id"] for item in result["projections"]],
            ["available", "degraded"],
        )

    def test_compatibility_api_serializes_canonical_envelopes(self) -> None:
        typed = self.service.projection_envelopes()
        compatibility = self.service.all_projections()

        expected = [item.to_dict() for item in typed]
        actual = compatibility["projections"]

        self.assertEqual(len(actual), len(expected))

        for expected_item, actual_item in zip(expected, actual):
            expected_item = dict(expected_item)
            actual_item = dict(actual_item)

            expected_item.pop("generated_at", None)
            actual_item.pop("generated_at", None)

            self.assertEqual(actual_item, expected_item)
    def test_empty_registry_is_not_configured(self) -> None:
        result = ExecutiveProjectionService(
            ProjectionRegistry()
        ).all_projections()
        self.assertEqual(result["provider_count"], 0)
        self.assertEqual(result["overall_status"], "not_configured")
        self.assertEqual(result["summary"]["available"], 0)


if __name__ == "__main__":
    unittest.main()
