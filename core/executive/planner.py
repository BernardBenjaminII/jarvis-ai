"""Capability-based deterministic mission planner for JARVIS Gen 2."""

from __future__ import annotations

from dataclasses import dataclass

from core.executive.models import Mission, MissionStatus, MissionTask, utc_now
from core.executive.registry import DirectorRegistry


@dataclass(frozen=True, slots=True)
class CapabilityRule:
    keywords: tuple[str, ...]
    capabilities: tuple[str, ...]
    action: str
    title: str


DEFAULT_RULES: tuple[CapabilityRule, ...] = (
    CapabilityRule(
        keywords=(
            "knowledge", "research", "find", "search", "explain",
            "summarize", "document", "book", "catalog",
        ),
        capabilities=("knowledge_search", "knowledge_retrieval"),
        action="search",
        title="Gather relevant knowledge",
    ),
    CapabilityRule(
        keywords=(
            "linux", "ubuntu", "windows", "macos", "kali",
            "system", "computer", "diagnose", "repair", "install",
        ),
        capabilities=("system_assessment",),
        action="assess",
        title="Assess system requirements",
    ),
)


class MissionPlanner:
    def __init__(
        self,
        registry: DirectorRegistry | None = None,
        rules: tuple[CapabilityRule, ...] = DEFAULT_RULES,
    ) -> None:
        self.registry = registry
        self._rules = rules

    def bind_registry(self, registry: DirectorRegistry) -> None:
        self.registry = registry

    def plan(self, mission: Mission) -> Mission:
        if not mission.objective.strip():
            raise ValueError("Mission objective cannot be empty")
        if self.registry is None:
            raise RuntimeError("MissionPlanner requires a DirectorRegistry")

        analyze = MissionTask(
            title="Analyze mission objective",
            director="executive",
            action="analyze",
            payload={"objective": mission.objective, "context": mission.context},
            required_capabilities=["mission_analysis"],
            routing_evidence={
                "selected_director": "executive",
                "reason": "Core executive responsibility.",
            },
        )

        delegated_tasks: list[MissionTask] = []
        objective_text = mission.objective.casefold()

        for rule in self._rules:
            if not any(keyword in objective_text for keyword in rule.keywords):
                continue

            decision = self.registry.select(rule.capabilities)
            delegated_tasks.append(
                MissionTask(
                    title=rule.title,
                    director=decision.selected_director,
                    action=rule.action,
                    payload={"objective": mission.objective, "context": mission.context},
                    depends_on=[analyze.task_id],
                    required_capabilities=list(rule.capabilities),
                    routing_evidence=decision.to_dict(),
                )
            )

        if not delegated_tasks:
            decision = self.registry.select(("general_reasoning",), fallback="executive")
            delegated_tasks.append(
                MissionTask(
                    title="Develop a general solution",
                    director=decision.selected_director,
                    action="reason",
                    payload={"objective": mission.objective, "context": mission.context},
                    depends_on=[analyze.task_id],
                    required_capabilities=["general_reasoning"],
                    routing_evidence=decision.to_dict(),
                )
            )

        synthesize = MissionTask(
            title="Synthesize mission result",
            director="executive",
            action="synthesize",
            payload={"objective": mission.objective},
            depends_on=[task.task_id for task in delegated_tasks],
            required_capabilities=["mission_synthesis"],
            routing_evidence={
                "selected_director": "executive",
                "reason": "Core executive responsibility.",
            },
        )

        mission.tasks = [analyze, *delegated_tasks, synthesize]
        mission.status = MissionStatus.PLANNED
        mission.updated_at = utc_now()
        return mission
