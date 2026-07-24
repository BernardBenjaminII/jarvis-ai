from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.operations import (
    EventKind,
    HealthAggregator,
    HealthState,
    MissionSnapshotAdapter,
    OperationsEvent,
    OperationsEventRegistry,
    OperationsService,
    ResourceCollector,
)


FIXED_TIME = datetime(2026, 7, 23, 0, 0, tzinfo=timezone.utc)


class StaticMissionProvider:
    def list_missions(self):
        return (
            {
                "mission_id": "mission-001",
                "name": "Establish Operations",
                "state": "active",
                "created_at": FIXED_TIME,
                "updated_at": FIXED_TIME,
                "source": "test-executive",
                "source_version": "1",
                "objectives": (),
            },
        )


class StaticResourceProvider:
    def collect_resources(self):
        return {
            "cpu_percent": 10.0,
            "memory_percent": 20.0,
            "disk_percent": 30.0,
            "load_average_1m": 0.5,
            "queue_depth": 2,
            "worker_count": 1,
        }


class MC1001OperationsTests(unittest.TestCase):
    def build_service(self):
        registry = OperationsEventRegistry()
        return OperationsService(
            missions=MissionSnapshotAdapter(StaticMissionProvider()),
            health=HealthAggregator(
                {"executive": lambda: {"state": "healthy", "detail": "ready"}}
            ),
            resources=ResourceCollector(StaticResourceProvider()),
            registry=registry,
            clock=lambda: FIXED_TIME,
        )

    def test_snapshot_is_immutable(self):
        snapshot = self.build_service().snapshot()
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = "failed"  # type: ignore[misc]

    def test_snapshot_is_deterministic(self):
        service = self.build_service()
        first = service.snapshot()
        second = service.snapshot()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_mission_is_projected(self):
        snapshot = self.build_service().snapshot()
        self.assertEqual(len(snapshot.missions), 1)
        self.assertEqual(snapshot.missions[0].mission_id, "mission-001")

    def test_health_is_aggregated(self):
        snapshot = self.build_service().snapshot()
        self.assertEqual(snapshot.health.state, HealthState.HEALTHY)

    def test_event_enters_timeline(self):
        service = self.build_service()
        service.record_event(
            OperationsEvent.create(
                kind=EventKind.MISSION_STARTED,
                summary="Mission started",
                subject_id="mission-001",
                occurred_at=FIXED_TIME,
                event_id="event-001",
            )
        )
        timeline = service.timeline()
        self.assertEqual(len(timeline.entries), 1)
        self.assertEqual(timeline.entries[0].event_id, "event-001")

    def test_serialization_is_json_compatible(self):
        payload = self.build_service().snapshot().to_dict()
        self.assertEqual(payload["state"], "ready")
        self.assertTrue(payload["generated_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
