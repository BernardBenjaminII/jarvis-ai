
from __future__ import annotations

import unittest

from core.executive.capabilities import (
    CapabilityGraph,
    CapabilityHealth,
    CapabilityMetadata,
    CapabilityObservabilityService,
    CapabilityOrchestrator,
    CapabilityRegistry,
    CapabilityRequirement,
    CapabilityRisk,
    PlanStatus,
)


def registry_fixture() -> CapabilityRegistry:
    return CapabilityRegistry(
        (
            CapabilityMetadata(
                capability_id="filesystem",
                name="Filesystem",
                owner="local",
                outputs=("files",),
                mission_types=("discover",),
                health=CapabilityHealth.READY,
            ),
            CapabilityMetadata(
                capability_id="knowledge",
                name="Knowledge",
                owner="local",
                inputs=("files",),
                outputs=("context",),
                dependencies=("filesystem",),
                mission_types=("summarize",),
                health=CapabilityHealth.READY,
                confidence=0.95,
                latency_ms=20,
            ),
            CapabilityMetadata(
                capability_id="remote-knowledge",
                name="Remote Knowledge",
                owner="external",
                inputs=("files",),
                outputs=("context",),
                permissions=("network",),
                dependencies=("filesystem",),
                mission_types=("summarize",),
                health=CapabilityHealth.READY,
                confidence=0.99,
                latency_ms=100,
                cost=2,
                risk=CapabilityRisk.MODERATE,
            ),
        )
    )


class Pack4B2Tests(unittest.TestCase):
    def test_registry_is_sorted_and_duplicate_safe(self) -> None:
        registry = registry_fixture()
        self.assertEqual(
            [item.capability_id for item in registry.all()],
            ["filesystem", "knowledge", "remote-knowledge"],
        )
        with self.assertRaises(ValueError):
            registry.register(registry.get("filesystem"))

    def test_graph_orders_dependencies_before_dependents(self) -> None:
        graph = CapabilityGraph(registry_fixture())
        self.assertEqual(graph.closure("knowledge"), ("filesystem", "knowledge"))
        self.assertEqual(graph.validate(), ())

    def test_selection_is_deterministic(self) -> None:
        orchestrator = CapabilityOrchestrator(registry_fixture())
        requirement = CapabilityRequirement(
            mission_type="summarize",
            required_inputs=("files",),
            required_outputs=("context",),
            permitted_permissions=("network",),
        )
        first = orchestrator.decide(requirement)
        second = orchestrator.decide(requirement)
        self.assertEqual(first.selection.fingerprint, second.selection.fingerprint)
        self.assertEqual(first.plan.fingerprint, second.plan.fingerprint)
        self.assertEqual(first.selection.selected_capability_id, "knowledge")

    def test_plan_contains_dependency_graph(self) -> None:
        decision = CapabilityOrchestrator(registry_fixture()).decide(
            CapabilityRequirement(
                mission_type="summarize",
                required_inputs=("files",),
                required_outputs=("context",),
            )
        )
        self.assertEqual(decision.plan.status, PlanStatus.PLANNED)
        self.assertEqual(
            [step.capability_id for step in decision.plan.steps],
            ["filesystem", "knowledge"],
        )

    def test_permission_boundary_blocks_external_candidate(self) -> None:
        registry = registry_fixture()
        registry.update_health("knowledge", CapabilityHealth.FAILED)
        decision = CapabilityOrchestrator(registry).decide(
            CapabilityRequirement(
                mission_type="summarize",
                required_inputs=("files",),
                required_outputs=("context",),
                permitted_permissions=(),
                maximum_risk=CapabilityRisk.LOW,
            )
        )
        self.assertIsNone(decision.selection.selected_capability_id)
        self.assertEqual(decision.plan.status, PlanStatus.BLOCKED)

    def test_observability_snapshot_reflects_live_health(self) -> None:
        registry = registry_fixture()
        registry.update_health("knowledge", CapabilityHealth.DEGRADED)
        snapshot = CapabilityObservabilityService(registry).snapshot()
        self.assertEqual(snapshot["capability_count"], 3)
        self.assertEqual(snapshot["health"]["degraded"], 1)
        self.assertEqual(snapshot["health"]["ready"], 2)


if __name__ == "__main__":
    unittest.main()
