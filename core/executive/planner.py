"""Deterministic first-generation mission planner for JARVIS Gen 2."""

from __future__ import annotations

from dataclasses import dataclass

from core.executive.models import Mission, MissionStatus, MissionTask, utc_now


@dataclass(frozen=True, slots=True)
class PlanningRule:
    keywords: tuple[str, ...]
    director: str
    action: str
    title: str


DEFAULT_RULES: tuple[PlanningRule, ...] = (
    PlanningRule(
        keywords=(
            "knowledge",
            "research",
            "find",
            "search",
            "explain",
            "summarize",
            "document",
            "book",
            "catalog",
        ),
        director="knowledge",
        action="search",
        title="Gather relevant knowledge",
    ),
    PlanningRule(
        keywords=(
            "linux",
            "ubuntu",
            "windows",
            "macos",
            "kali",
            "system",
            "computer",
            "diagnose",
            "repair",
            "install",
        ),
        director="system",
        action="assess",
        title="Assess system requirements",
    ),
)


class MissionPlanner:
    """
    Produces deterministic, auditable plans.

    This planner intentionally avoids LLM dependence. A later Gen 2 phase can
    add an LLM planner behind the same interface without changing the engine.
    """

    def __init__(
        self,
        rules: tuple[PlanningRule, ...] = DEFAULT_RULES,
    ) -> None:
        self._rules = rules

    def plan(self, mission: Mission) -> Mission:
        if not mission.objective.strip():
            raise ValueError("Mission objective cannot be empty")

        analyze = MissionTask(
            title="Analyze mission objective",
            director="executive",
            action="analyze",
            payload={
                "objective": mission.objective,
                "context": mission.context,
            },
        )

        delegated_tasks: list[MissionTask] = []
        objective_text = mission.objective.casefold()

        for rule in self._rules:
            if any(keyword in objective_text for keyword in rule.keywords):
                delegated_tasks.append(
                    MissionTask(
                        title=rule.title,
                        director=rule.director,
                        action=rule.action,
                        payload={
                            "objective": mission.objective,
                            "context": mission.context,
                        },
                        depends_on=[analyze.task_id],
                    )
                )

        if not delegated_tasks:
            delegated_tasks.append(
                MissionTask(
                    title="Develop a general solution",
                    director="executive",
                    action="reason",
                    payload={
                        "objective": mission.objective,
                        "context": mission.context,
                    },
                    depends_on=[analyze.task_id],
                )
            )

        synthesize = MissionTask(
            title="Synthesize mission result",
            director="executive",
            action="synthesize",
            payload={"objective": mission.objective},
            depends_on=[task.task_id for task in delegated_tasks],
        )

        mission.tasks = [analyze, *delegated_tasks, synthesize]
        mission.status = MissionStatus.PLANNED
        mission.updated_at = utc_now()
        return mission
