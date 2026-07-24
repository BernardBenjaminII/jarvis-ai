from __future__ import annotations

import unittest

from core.integration.bus import ExecutiveProjectionBus
from core.integration.readiness import ReadinessColor, ReadinessLevel, normalize_projection_readiness


class FakeProjectionService:
    def __init__(self) -> None:
        self.status = "available"

    def all_projections(self) -> dict:
        return {
            "projections": {
                "knowledge": {
                    "projection_id": "knowledge",
                    "health": {
                        "status": self.status,
                        "summary": "Knowledge retrieval is available.",
                        "details": {"retrieval": True},
                        "warnings": [],
                        "errors": [],
                    },
                    "data": {"retrieval": {"ready": True}},
                },
                "operations": {
                    "projection_id": "operations",
                    "health": {
                        "status": "degraded",
                        "summary": "Operations is usable with caution.",
                        "details": {},
                        "warnings": ["worker capacity reduced"],
                        "errors": [],
                    },
                    "data": {},
                },
            }
        }


class GenesisVIA3ProjectionBusTests(unittest.TestCase):
    def test_green_mapping(self) -> None:
        result = normalize_projection_readiness("knowledge", {"health": {"status": "available"}})
        self.assertEqual(result.color, ReadinessColor.GREEN)
        self.assertEqual(result.level, ReadinessLevel.GOOD)
        self.assertTrue(result.ready)

    def test_yellow_mapping(self) -> None:
        result = normalize_projection_readiness("knowledge", {"health": {"status": "degraded"}})
        self.assertEqual(result.color, ReadinessColor.YELLOW)
        self.assertTrue(result.ready)

    def test_red_mapping(self) -> None:
        result = normalize_projection_readiness("knowledge", {"health": {"status": "unavailable"}})
        self.assertEqual(result.color, ReadinessColor.RED)
        self.assertFalse(result.ready)

    def test_bus_aggregate(self) -> None:
        payload = ExecutiveProjectionBus(FakeProjectionService()).snapshot().to_dict()
        self.assertEqual(list(payload["projections"]), ["knowledge", "operations"])
        self.assertEqual(payload["readiness"]["knowledge"]["color"], "green")
        self.assertEqual(payload["readiness"]["operations"]["color"], "yellow")
        self.assertEqual(payload["overall"]["color"], "yellow")

    def test_revision_stability(self) -> None:
        bus = ExecutiveProjectionBus(FakeProjectionService())
        first = bus.snapshot()
        second = bus.snapshot()
        self.assertEqual(first.revision, second.revision)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_revision_change(self) -> None:
        service = FakeProjectionService()
        bus = ExecutiveProjectionBus(service)
        first = bus.snapshot()
        service.status = "unavailable"
        second = bus.snapshot(force=True)
        self.assertGreater(second.revision, first.revision)
        self.assertEqual(second.overall.color, ReadinessColor.RED)

    def test_manifest(self) -> None:
        manifest = ExecutiveProjectionBus(FakeProjectionService()).manifest()
        self.assertEqual(manifest["projection_count"], 2)
        self.assertIn("knowledge", manifest["projection_ids"])


if __name__ == "__main__":
    unittest.main()
