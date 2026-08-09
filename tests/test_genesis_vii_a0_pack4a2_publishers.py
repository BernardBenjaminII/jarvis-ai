"""Genesis VII-A0 Pack 4A-2 certification tests."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.capabilities.registry import CapabilityRegistry
from core.executive.capabilities import DirectorReadiness
from core.executive.events import ExecutiveEventBus
from core.executive.registry import DirectorRegistry
from core.executive.timeline import (
    ExecutiveTimelineRepository,
    TimelineEventKind,
)
from core.operations import HealthAggregator


@dataclass
class FakeCapability:
    name: str
    provides: set[str]
    requires: set[str]
    order: int = 100


class GenesisVIIA0Pack4A2Tests(unittest.TestCase):
    def build_bus(self, root: Path) -> ExecutiveEventBus:
        return ExecutiveEventBus(
            repository=ExecutiveTimelineRepository(root),
            event_id_factory=lambda sequence: f"event-{sequence:04d}",
        )

    def test_capability_registration_publishes(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            registry = CapabilityRegistry(event_bus=bus)
            registry.register(
                FakeCapability(
                    name="filesystem",
                    provides={"filesystem.read"},
                    requires=set(),
                )
            )
            event = bus.events[-1]
            self.assertIs(
                event.kind,
                TimelineEventKind.CAPABILITY_REGISTERED,
            )
            self.assertEqual(event.payload["name"], "filesystem")

    def test_director_lifecycle_publishes(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            registry = DirectorRegistry(event_bus=bus)
            registry.register(
                "executive",
                lambda mission, task: None,
                capabilities={"planning"},
            )
            registry.set_readiness(
                "executive",
                DirectorReadiness.DEGRADED,
            )
            registry.unregister("executive")
            self.assertEqual(
                [event.kind for event in bus.events],
                [
                    TimelineEventKind.DIRECTOR_REGISTERED,
                    TimelineEventKind.DIRECTOR_READINESS_CHANGED,
                    TimelineEventKind.DIRECTOR_UNREGISTERED,
                ],
            )

    def test_health_publishes_only_transitions(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            state = {"value": "healthy"}
            aggregator = HealthAggregator(
                {
                    "runtime": lambda: {
                        "state": state["value"],
                        "detail": "runtime",
                    }
                },
                event_bus=bus,
            )
            aggregator.collect()
            aggregator.collect()
            state["value"] = "degraded"
            aggregator.collect()
            self.assertEqual(
                [event.kind for event in bus.events],
                [
                    TimelineEventKind.HEALTH_STATE_CHANGED,
                    TimelineEventKind.HEALTH_STATE_CHANGED,
                ],
            )
            self.assertEqual(
                bus.events[-1].payload["previous_state"],
                "healthy",
            )
            self.assertEqual(
                bus.events[-1].payload["current_state"],
                "degraded",
            )


if __name__ == "__main__":
    unittest.main()
