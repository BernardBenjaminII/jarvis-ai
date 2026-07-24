"""Capability-routed deterministic mission planner for JARVIS Gen 2."""
from __future__ import annotations

from core.executive.models import Mission, MissionStatus, MissionTask, utc_now
from core.executive.registry import DirectorRegistry
from core.executive.routing import CapabilityRouter


class MissionPlanner:
    def __init__(self, registry: DirectorRegistry | None = None, router: CapabilityRouter | None = None, **_legacy) -> None:
        self.registry = registry
        self.router = router
        if registry is not None and router is None:
            self.router = CapabilityRouter(registry)

    def bind_registry(self, registry: DirectorRegistry) -> None:
        self.registry = registry
        self.router = CapabilityRouter(registry)

    def plan(self, mission: Mission) -> Mission:
        if not mission.objective.strip():
            raise ValueError("Mission objective cannot be empty")
        if self.registry is None or self.router is None:
            raise RuntimeError("MissionPlanner requires a DirectorRegistry")

        analyze = MissionTask(
            title="Analyze mission objective", director="executive", action="analyze",
            payload={"objective": mission.objective, "context": mission.context},
            required_capabilities=["mission_analysis"],
            routing_evidence={"selected_director":"executive","reason":"Core executive responsibility.","router":"convergence_c3"},
        )
        routes = self.router.route(mission.objective, hints=mission.context.get("routing_hints", ()))
        delegated=[]
        for route in routes:
            delegated.append(MissionTask(
                title=route.title, director=route.director, action=route.action,
                payload={"objective": mission.objective, "context": mission.context, "capability_profile": route.profile},
                depends_on=[analyze.task_id], required_capabilities=list(route.capabilities), routing_evidence=dict(route.evidence),
            ))
        synthesize = MissionTask(
            title="Synthesize mission result", director="executive", action="synthesize",
            payload={"objective": mission.objective}, depends_on=[task.task_id for task in delegated],
            required_capabilities=["mission_synthesis"],
            routing_evidence={"selected_director":"executive","reason":"Core executive responsibility.","router":"convergence_c3"},
        )
        mission.tasks=[analyze,*delegated,synthesize]
        mission.status=MissionStatus.PLANNED
        mission.updated_at=utc_now()
        return mission
