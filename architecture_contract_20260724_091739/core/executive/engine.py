"""Dependency-aware execution engine for JARVIS missions."""

from __future__ import annotations

from core.executive.contracts import InvalidMissionPlanError
from core.executive.models import (
    Mission,
    MissionStatus,
    MissionTask,
    TaskStatus,
    utc_now,
)
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class MissionEngine:
    """Executes mission tasks and persists every state transition."""

    def __init__(
        self,
        registry: DirectorRegistry,
        store: MissionStore,
    ) -> None:
        self.registry = registry
        self.store = store

    def execute(self, mission: Mission) -> Mission:
        self._validate_plan(mission)

        mission.status = MissionStatus.RUNNING
        mission.started_at = mission.started_at or utc_now()
        mission.updated_at = utc_now()
        self._persist(mission, "mission_started", {})

        while True:
            pending = [
                task
                for task in mission.tasks
                if task.status in {TaskStatus.PENDING, TaskStatus.READY}
            ]
            if not pending:
                break

            progress = False
            for task in pending:
                dependency_states = self._dependency_states(mission, task)

                if any(
                    state in {TaskStatus.FAILED, TaskStatus.BLOCKED}
                    for state in dependency_states
                ):
                    task.status = TaskStatus.BLOCKED
                    task.error = "One or more dependencies failed or were blocked."
                    task.completed_at = utc_now()
                    mission.updated_at = utc_now()
                    self._persist(
                        mission,
                        "task_blocked",
                        {"task_id": task.task_id, "error": task.error},
                    )
                    progress = True
                    continue

                if not all(
                    state == TaskStatus.COMPLETED
                    for state in dependency_states
                ):
                    continue

                task.status = TaskStatus.READY
                self._run_task(mission, task)
                progress = True

            if not progress:
                mission.status = MissionStatus.BLOCKED
                mission.error = (
                    "Mission made no progress. Check for unresolved or cyclic "
                    "task dependencies."
                )
                mission.updated_at = utc_now()
                self._persist(
                    mission,
                    "mission_blocked",
                    {"error": mission.error},
                )
                return mission

        failed_tasks = [
            task for task in mission.tasks if task.status == TaskStatus.FAILED
        ]
        blocked_tasks = [
            task for task in mission.tasks if task.status == TaskStatus.BLOCKED
        ]

        if failed_tasks:
            mission.status = MissionStatus.FAILED
            mission.error = f"{len(failed_tasks)} task(s) failed."
        elif blocked_tasks:
            mission.status = MissionStatus.BLOCKED
            mission.error = f"{len(blocked_tasks)} task(s) were blocked."
        else:
            mission.status = MissionStatus.COMPLETED
            mission.summary = self._mission_summary(mission)
            mission.completed_at = utc_now()

        mission.updated_at = utc_now()
        self._persist(
            mission,
            f"mission_{mission.status.value}",
            {
                "summary": mission.summary,
                "error": mission.error,
            },
        )
        return mission

    def _run_task(self, mission: Mission, task: MissionTask) -> None:
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        mission.updated_at = utc_now()
        self._persist(
            mission,
            "task_started",
            {
                "task_id": task.task_id,
                "director": task.director,
                "action": task.action,
            },
        )

        try:
            handler = self.registry.resolve(task.director)
            execution = handler(mission, task)
        except Exception as exc:  # engine boundary
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.completed_at = utc_now()
            mission.updated_at = utc_now()
            self._persist(
                mission,
                "task_failed",
                {"task_id": task.task_id, "error": task.error},
            )
            return

        task.completed_at = utc_now()
        mission.updated_at = utc_now()

        if execution.success:
            task.status = TaskStatus.COMPLETED
            task.result = execution.output
            task.error = None
            self._persist(
                mission,
                "task_completed",
                {"task_id": task.task_id, "result": task.result},
            )
        else:
            task.status = TaskStatus.FAILED
            task.error = execution.error or "Director returned failure."
            self._persist(
                mission,
                "task_failed",
                {"task_id": task.task_id, "error": task.error},
            )

    def _dependency_states(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> list[TaskStatus]:
        by_id = {candidate.task_id: candidate for candidate in mission.tasks}
        return [by_id[task_id].status for task_id in task.depends_on]

    def _validate_plan(self, mission: Mission) -> None:
        if not mission.tasks:
            raise InvalidMissionPlanError("Mission has no tasks")

        task_ids = [task.task_id for task in mission.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise InvalidMissionPlanError("Mission contains duplicate task IDs")

        known = set(task_ids)
        for task in mission.tasks:
            missing = set(task.depends_on) - known
            if missing:
                raise InvalidMissionPlanError(
                    f"Task {task.task_id} has missing dependencies: "
                    + ", ".join(sorted(missing))
                )
            if task.task_id in task.depends_on:
                raise InvalidMissionPlanError(
                    f"Task {task.task_id} depends on itself"
                )

        visiting: set[str] = set()
        visited: set[str] = set()
        dependencies = {
            task.task_id: tuple(task.depends_on) for task in mission.tasks
        }

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise InvalidMissionPlanError(
                    "Mission plan contains a dependency cycle"
                )
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency_id in dependencies[task_id]:
                visit(dependency_id)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in task_ids:
            visit(task_id)

        self.registry.require(task.director for task in mission.tasks)

    def _persist(
        self,
        mission: Mission,
        event_type: str,
        payload: dict,
    ) -> None:
        self.store.save(mission)
        self.store.record_event(
            mission.mission_id,
            event_type,
            payload,
            utc_now(),
        )

    @staticmethod
    def _mission_summary(mission: Mission) -> dict:
        return {
            "objective": mission.objective,
            "status": mission.status.value,
            "task_count": len(mission.tasks),
            "completed_tasks": sum(
                task.status == TaskStatus.COMPLETED for task in mission.tasks
            ),
            "directors_used": sorted(
                {task.director for task in mission.tasks}
            ),
        }
