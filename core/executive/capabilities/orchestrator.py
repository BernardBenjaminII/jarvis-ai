
"""Executive entry point for capability selection and planning."""

from __future__ import annotations

from .graph import CapabilityGraph
from .models import CapabilityRequirement, OrchestrationDecision
from .planner import CapabilityPlanner
from .registry import CapabilityRegistry
from .selector import CapabilitySelector


class CapabilityOrchestrator:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry
        self.graph = CapabilityGraph(registry)
        self.selector = CapabilitySelector(registry)
        self.planner = CapabilityPlanner(registry, self.graph)

    def decide(self, requirement: CapabilityRequirement) -> OrchestrationDecision:
        findings = self.graph.validate()
        if findings:
            raise RuntimeError("Invalid capability graph: " + "; ".join(findings))
        selection = self.selector.select(requirement)
        plan = self.planner.plan(
            mission_type=requirement.mission_type,
            selected_capability_id=selection.selected_capability_id,
        )
        return OrchestrationDecision(
            requirement=requirement,
            selection=selection,
            plan=plan,
        )
