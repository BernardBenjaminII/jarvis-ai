"""Top-level Executive Director facade for JARVIS Gen 2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.executive.capabilities import DirectorReadiness
from core.executive.engine import MissionEngine
from core.executive.handlers import (
    KnowledgeHandler,
    KnowledgeSearch,
    executive_handler,
    placeholder_system_handler,
)
from core.executive.models import Mission, MissionStatus, utc_now
from core.executive.planner import MissionPlanner
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class ExecutiveDirector:
    def __init__(
        self,
        *,
        database_path: str | Path,
        registry: DirectorRegistry | None = None,
        planner: MissionPlanner | None = None,
        knowledge_search: KnowledgeSearch | None = None,
    ) -> None:
        self.registry = registry or DirectorRegistry()
        self.store = MissionStore(database_path)

        if not self.registry.contains("executive"):
            self.registry.register(
                "executive",
                executive_handler,
                capabilities={"mission_analysis", "mission_synthesis", "general_reasoning"},
                description=(
                    "Supervises missions, performs general reasoning, and "
                    "synthesizes subordinate results."
                ),
                priority=10,
            )

        if not self.registry.contains("knowledge"):
            self.registry.register(
                "knowledge",
                KnowledgeHandler(search=knowledge_search),
                capabilities={
                    "knowledge_search",
                    "knowledge_retrieval",
                    "knowledge_summarization",
                },
                description=(
                    "Retrieves and summarizes information from the JARVIS "
                    "Knowledge Engine."
                ),
                priority=20,
                readiness=(
                    DirectorReadiness.READY
                    if knowledge_search is not None
                    else DirectorReadiness.DEGRADED
                ),
                metadata={
                    "integration": "live" if knowledge_search is not None else "bridge_ready"
                },
            )

        if not self.registry.contains("system"):
            self.registry.register(
                "system",
                placeholder_system_handler,
                capabilities={"system_assessment", "platform_analysis"},
                description=(
                    "Assesses host-system requirements without modifying "
                    "the operating system."
                ),
                priority=30,
                readiness=DirectorReadiness.DEGRADED,
                metadata={"execution_mode": "assessment_only"},
            )

        self.planner = planner or MissionPlanner(registry=self.registry)
        self.planner.bind_registry(self.registry)
        self.engine = MissionEngine(self.registry, self.store)

    def create_mission(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Mission:
        mission = Mission(objective=objective.strip(), context=context or {})
        if not mission.objective:
            raise ValueError("Mission objective cannot be empty")
        self.store.save(mission)
        self.store.record_event(
            mission.mission_id,
            "mission_created",
            {"objective": mission.objective},
            utc_now(),
        )
        return mission

    def plan_mission(self, mission: Mission) -> Mission:
        planned = self.planner.plan(mission)
        self.store.save(planned)
        self.store.record_event(
            planned.mission_id,
            "mission_planned",
            {
                "task_count": len(planned.tasks),
                "directors": sorted({task.director for task in planned.tasks}),
                "routing": [
                    {
                        "task_id": task.task_id,
                        "director": task.director,
                        "required_capabilities": task.required_capabilities,
                        "routing_evidence": task.routing_evidence,
                    }
                    for task in planned.tasks
                ],
            },
            utc_now(),
        )
        return planned

    def submit(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
        execute: bool = True,
    ) -> Mission:
        mission = self.create_mission(objective, context=context)
        mission = self.plan_mission(mission)
        if execute:
            mission = self.engine.execute(mission)
        return mission

    def execute_mission(self, mission_id: str) -> Mission:
        mission = self.store.load(mission_id)
        if mission.status == MissionStatus.DRAFT:
            mission = self.plan_mission(mission)
        if mission.status in {MissionStatus.COMPLETED, MissionStatus.CANCELLED}:
            return mission
        return self.engine.execute(mission)

    def get_mission(self, mission_id: str) -> Mission:
        return self.store.load(mission_id)

    def list_missions(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mission]:
        return self.store.list(status=status, limit=limit)

    def mission_events(self, mission_id: str) -> list[dict[str, Any]]:
        self.store.load(mission_id)
        return self.store.events(mission_id)

    def director_catalog(self) -> list[dict[str, Any]]:
        return [descriptor.to_dict() for descriptor in self.registry.descriptors()]
