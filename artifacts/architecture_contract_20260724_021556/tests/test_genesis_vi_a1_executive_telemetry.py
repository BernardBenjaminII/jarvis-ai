"""Regression tests for Genesis VI-A1 Executive telemetry integration."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.operations import (
    ExecutiveSnapshot,
    ExecutiveState,
    ExecutiveTelemetryAdapter,
    HealthAggregator,
    MissionSnapshotAdapter,
    OperationalState,
    OperationsService,
    ResourceCollector,
)

FIXED_TIME = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


class StaticExecutiveProvider:
    """Deterministic Executive provider used by the certification fixture."""

    def collect_executive_state(self):
        return {
            "state": "reasoning",
            "readiness": 0.91,
            "detail": "Evaluating validated evidence.",
            "active_mission_id": "mission-001",
            "active_objective_id": "objective-001",
            "current_activity": "Hypothesis evaluation",
            "pending_decisions": 2,
            "pending_recommendations": 1,
            "observation_count": 14,
            "inference_count": 4,
            "plan_count": 1,
            "last_transition_at": FIXED_TIME,
            "source": "genesis-vi-a1-test",
            "source_version": "1",
        }


class FailingExecutiveProvider:
    """Provider boundary fixture proving failures remain UI-safe."""

    def collect_executive_state(self):
        raise RuntimeError("executive provider unavailable")


class StaticMissionProvider:
    def list_missions(self):
        return (
            {
                "mission_id": "mission-001",
                "name": "Establish Executive Telemetry",
                "state": "active",
                "created_at": FIXED_TIME,
                "updated_at": FIXED_TIME,
                "source": "genesis-vi-a1-test",
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


class GenesisVIA1ExecutiveTelemetryTests(unittest.TestCase):
    def build_service(
        self,
        provider=None,
        health_state: str = "healthy",
    ) -> OperationsService:
        executive_provider = provider or StaticExecutiveProvider()
        return OperationsService(
            executive=ExecutiveTelemetryAdapter(executive_provider),
            missions=MissionSnapshotAdapter(StaticMissionProvider()),
            health=HealthAggregator(
                {
                    "executive": lambda: {
                        "state": health_state,
                        "detail": "Executive boundary checked.",
                    }
                }
            ),
            resources=ResourceCollector(StaticResourceProvider()),
            clock=lambda: FIXED_TIME,
        )

    def test_executive_snapshot_is_immutable(self):
        snapshot = self.build_service().executive()

        self.assertIsInstance(snapshot, ExecutiveSnapshot)
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = ExecutiveState.FAILED  # type: ignore[misc]

    def test_executive_telemetry_is_projected(self):
        snapshot = self.build_service().snapshot()

        self.assertEqual(snapshot.executive.state, ExecutiveState.REASONING)
        self.assertEqual(snapshot.executive.readiness, 0.91)
        self.assertEqual(snapshot.executive.active_mission_id, "mission-001")
        self.assertEqual(snapshot.executive.active_objective_id, "objective-001")
        self.assertEqual(snapshot.executive.pending_decisions, 2)
        self.assertEqual(snapshot.executive.observation_count, 14)

    def test_operations_payload_contains_executive_section(self):
        payload = self.build_service().snapshot().to_dict()

        self.assertIn("executive", payload)
        self.assertEqual(payload["executive"]["state"], "reasoning")
        self.assertEqual(payload["executive"]["readiness"], 0.91)
        self.assertEqual(payload["executive"]["captured_at"], "2026-07-23T12:00:00Z")

    def test_existing_operations_payload_contract_remains_available(self):
        payload = self.build_service().snapshot().to_dict()

        for field in (
            "state",
            "missions",
            "health",
            "resources",
            "timeline",
            "alerts",
            "generated_at",
            "fingerprint",
        ):
            self.assertIn(field, payload)

        self.assertEqual(payload["missions"][0]["mission_id"], "mission-001")
        self.assertEqual(payload["resources"]["mission_count"], 1)
        self.assertEqual(len(payload["fingerprint"]), 64)

    def test_snapshot_and_fingerprint_are_deterministic(self):
        service = self.build_service()

        first = service.snapshot()
        second = service.snapshot()

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_executive_runtime_state_drives_operations_state(self):
        snapshot = self.build_service().snapshot()

        self.assertEqual(snapshot.state, OperationalState.READY)

        stopped_provider = StaticExecutiveProvider()
        original = stopped_provider.collect_executive_state
        stopped_provider.collect_executive_state = lambda: {
            **original(),
            "state": "stopped",
        }
        stopped = self.build_service(stopped_provider).snapshot()
        self.assertEqual(stopped.state, OperationalState.STOPPED)

    def test_health_degradation_still_drives_operations_state(self):
        snapshot = self.build_service(health_state="degraded").snapshot()

        self.assertEqual(snapshot.state, OperationalState.DEGRADED)
        self.assertEqual(len(snapshot.alerts), 1)
        self.assertEqual(snapshot.alerts[0].alert_id, "health:executive")

    def test_provider_failure_is_contained(self):
        snapshot = self.build_service(FailingExecutiveProvider()).snapshot()

        self.assertEqual(snapshot.executive.state, ExecutiveState.FAILED)
        self.assertEqual(snapshot.executive.readiness, 0.0)
        self.assertIn("RuntimeError", snapshot.executive.detail)
        self.assertEqual(snapshot.state, OperationalState.FAILED)

    def test_default_service_remains_constructible(self):
        payload = OperationsService(clock=lambda: FIXED_TIME).snapshot().to_dict()

        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["executive"]["state"], "ready")
        self.assertEqual(len(payload["fingerprint"]), 64)


if __name__ == "__main__":
    unittest.main()
