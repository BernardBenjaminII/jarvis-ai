"""Built-in director handlers for the Gen 2 executive foundation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.executive.models import Mission, MissionTask, TaskExecutionResult


def executive_handler(
    mission: Mission,
    task: MissionTask,
) -> TaskExecutionResult:
    """Handle core analysis, reasoning, and synthesis actions."""
    if task.action == "analyze":
        return TaskExecutionResult(
            success=True,
            output={
                "objective": mission.objective,
                "context_keys": sorted(mission.context),
                "objective_length": len(mission.objective),
                "assessment": "Mission objective accepted and normalized.",
            },
        )

    if task.action == "reason":
        return TaskExecutionResult(
            success=True,
            output={
                "approach": (
                    "General executive reasoning path selected because no "
                    "specialist planning rule matched the objective."
                ),
                "objective": mission.objective,
            },
        )

    if task.action == "synthesize":
        completed_outputs = [
            {
                "task_id": candidate.task_id,
                "title": candidate.title,
                "director": candidate.director,
                "output": candidate.result,
            }
            for candidate in mission.tasks
            if candidate.task_id != task.task_id and candidate.result is not None
        ]
        return TaskExecutionResult(
            success=True,
            output={
                "objective": mission.objective,
                "completed_task_count": len(completed_outputs),
                "task_outputs": completed_outputs,
            },
        )

    return TaskExecutionResult(
        success=False,
        error=f"Unsupported executive action: {task.action}",
    )


def placeholder_system_handler(
    mission: Mission,
    task: MissionTask,
) -> TaskExecutionResult:
    """
    Safe Phase I system adapter.

    It prepares delegation data but performs no host changes. A later phase
    will connect this contract to OS-specific specialists and guarded tools.
    """
    return TaskExecutionResult(
        success=True,
        output={
            "mode": "assessment_only",
            "objective": mission.objective,
            "requested_action": task.action,
            "message": (
                "System task accepted. Active OS execution is intentionally "
                "disabled in Gen 2 Phase I."
            ),
        },
    )


KnowledgeSearch = Callable[[str, dict[str, Any]], dict[str, Any]]


class KnowledgeHandler:
    """
    Bridge contract for the existing Knowledge Director.

    Pass a callable with signature:
        search(objective: str, context: dict) -> dict

    Until connected, the handler remains safe and explicit rather than
    guessing the current Knowledge Director API.
    """

    def __init__(self, search: KnowledgeSearch | None = None) -> None:
        self._search = search

    def __call__(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> TaskExecutionResult:
        if self._search is None:
            return TaskExecutionResult(
                success=True,
                output={
                    "mode": "bridge_ready",
                    "objective": mission.objective,
                    "requested_action": task.action,
                    "message": (
                        "Knowledge task routed successfully. Connect the "
                        "existing Knowledge Director through KnowledgeHandler."
                    ),
                },
            )

        try:
            output = self._search(mission.objective, mission.context)
        except Exception as exc:  # boundary: external director integration
            return TaskExecutionResult(
                success=False,
                error=f"Knowledge Director failed: {exc}",
            )

        if not isinstance(output, dict):
            output = {"result": output}

        return TaskExecutionResult(success=True, output=output)
