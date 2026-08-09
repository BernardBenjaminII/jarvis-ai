
"""Dependency-aware deterministic capability planner."""

from __future__ import annotations

from .graph import CapabilityGraph, CapabilityGraphError
from .models import CapabilityPlan, PlanStatus, PlanStep
from .registry import CapabilityRegistry


class CapabilityPlanner:
    def __init__(self, registry: CapabilityRegistry, graph: CapabilityGraph) -> None:
        self._registry = registry
        self._graph = graph

    def plan(self, *, mission_type: str, selected_capability_id: str | None) -> CapabilityPlan:
        if selected_capability_id is None:
            return CapabilityPlan(
                mission_type=mission_type,
                status=PlanStatus.BLOCKED,
                steps=(),
                blocked_reasons=("No eligible capability satisfies the mission.",),
            )
        try:
            closure = self._graph.closure(selected_capability_id)
        except (CapabilityGraphError, KeyError) as exc:
            return CapabilityPlan(
                mission_type=mission_type,
                status=PlanStatus.BLOCKED,
                steps=(),
                blocked_reasons=(str(exc),),
            )

        blocked = []
        for capability_id in closure:
            capability = self._registry.get(capability_id)
            if capability.health.value in {"failed", "disabled"}:
                blocked.append(
                    f"{capability_id} is {capability.health.value}."
                )

        if blocked:
            return CapabilityPlan(
                mission_type=mission_type,
                status=PlanStatus.BLOCKED,
                steps=(),
                blocked_reasons=tuple(blocked),
            )

        steps = tuple(
            PlanStep(
                sequence=index,
                capability_id=capability_id,
                depends_on=self._registry.get(capability_id).dependencies,
                reason=(
                    "Selected mission capability."
                    if capability_id == selected_capability_id
                    else f"Dependency required by {selected_capability_id}."
                ),
            )
            for index, capability_id in enumerate(closure, start=1)
        )
        return CapabilityPlan(
            mission_type=mission_type,
            status=PlanStatus.PLANNED,
            steps=steps,
        )
