"""Executive conversation orchestration with C-4 knowledge grounding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.conversation.contracts import ConversationTraceEvent, ExecutiveRequestContext
from core.conversation.grounding import CatalogGroundingService, GroundingResult
from core.executive.director import ExecutiveDirector
from core.executive.models import Mission

SynthesisHandler = Callable[[str], Any]


@dataclass(frozen=True, slots=True)
class DirectorAssignment:
    objective_id: str
    objective: str
    mission_id: str
    status: str
    directors: tuple[str, ...]
    tasks: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "objective": self.objective,
            "mission_id": self.mission_id,
            "status": self.status,
            "directors": list(self.directors),
            "tasks": [dict(task) for task in self.tasks],
            "summary": dict(self.summary),
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    answer: str
    assignments: tuple[DirectorAssignment, ...]
    trace: tuple[ConversationTraceEvent, ...]
    grounding: GroundingResult | None = None

    def metadata(self) -> dict[str, Any]:
        metadata = {
            "orchestration": "knowledge_grounded_director_activation" if self.grounding else "director_activation",
            "missions": [item.to_dict() for item in self.assignments],
            "directors_activated": sorted(
                {director for item in self.assignments for director in item.directors}
            ),
        }
        if self.grounding is not None:
            metadata["knowledge_grounding"] = self.grounding.to_dict()
        return metadata


class ExecutiveConversationOrchestrator:
    """Ground, delegate, execute, and synthesize each operator request."""

    def __init__(
        self,
        *,
        director: ExecutiveDirector,
        synthesis_handler: SynthesisHandler,
        grounding_service: CatalogGroundingService | None = None,
    ) -> None:
        self.director = director
        self.synthesis_handler = synthesis_handler
        self.grounding_service = grounding_service

    def execute(self, context: ExecutiveRequestContext) -> OrchestrationResult:
        trace: list[ConversationTraceEvent] = []
        assignments: list[DirectorAssignment] = []
        grounding: GroundingResult | None = None

        if self.grounding_service is not None:
            trace.append(ConversationTraceEvent(
                stage="knowledge.grounding",
                status="processing",
                detail="Searching the canonical knowledge catalog for objective evidence.",
            ))
            grounding = self.grounding_service.ground(context)
            trace.append(ConversationTraceEvent(
                stage="knowledge.grounding",
                status="completed" if grounding.evidence else "gap",
                detail=(
                    f"Retrieved {len(grounding.evidence)} evidence record(s); "
                    f"declared {len(grounding.gaps)} knowledge gap(s)."
                ),
                data={
                    "status": grounding.status,
                    "evidence_count": len(grounding.evidence),
                    "gap_count": len(grounding.gaps),
                },
            ))

        for objective in context.objectives:
            trace.append(ConversationTraceEvent(
                stage="director.mission.created",
                status="processing",
                detail=f"Creating mission for objective {objective.ordinal}.",
                data={"objective_id": objective.objective_id},
            ))
            objective_grounding = grounding.for_objective(objective.objective_id) if grounding else None
            mission = self.director.submit(
                objective.text,
                context={
                    "request_id": context.request_id,
                    "session_id": context.session_id,
                    "channel": context.channel,
                    "mode": context.mode,
                    "objective_id": objective.objective_id,
                    "routing_hints": list(objective.routing_hints),
                    "knowledge_grounding": (
                        None if objective_grounding is None else objective_grounding.to_dict()
                    ),
                    **dict(context.metadata),
                },
                execute=True,
            )
            assignment = self._assignment(objective.objective_id, mission)
            assignments.append(assignment)
            trace.append(ConversationTraceEvent(
                stage="director.mission.completed",
                status="completed" if mission.status.value == "completed" else mission.status.value,
                detail=(
                    f"Mission {mission.mission_id} completed through "
                    f"{', '.join(assignment.directors) or 'executive'} director(s)."
                ),
                data={
                    "mission_id": mission.mission_id,
                    "directors": list(assignment.directors),
                    "status": mission.status.value,
                },
            ))

        trace.append(ConversationTraceEvent(
            stage="executive.synthesis",
            status="processing",
            detail="Synthesizing director activity and grounded evidence.",
        ))
        synthesis_input = (
            grounding.synthesis_input(context.operator_input)
            if grounding is not None
            else context.operator_input
        )
        answer = self._normalize_answer(self.synthesis_handler(synthesis_input))
        trace.append(ConversationTraceEvent(
            stage="executive.synthesis",
            status="completed",
            detail="Unified JARVIS response completed.",
        ))
        return OrchestrationResult(
            answer=answer,
            assignments=tuple(assignments),
            trace=tuple(trace),
            grounding=grounding,
        )

    @staticmethod
    def _assignment(objective_id: str, mission: Mission) -> DirectorAssignment:
        tasks = tuple({
            "task_id": task.task_id,
            "title": task.title,
            "director": task.director,
            "action": task.action,
            "status": task.status.value,
            "required_capabilities": list(task.required_capabilities),
            "routing_evidence": dict(task.routing_evidence),
            "result": task.result,
            "error": task.error,
        } for task in mission.tasks)
        return DirectorAssignment(
            objective_id=objective_id,
            objective=mission.objective,
            mission_id=mission.mission_id,
            status=mission.status.value,
            directors=tuple(sorted({task.director for task in mission.tasks})),
            tasks=tasks,
            summary=dict(mission.summary or {}),
            error=mission.error,
        )

    @staticmethod
    def _normalize_answer(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("answer", "response", "message", "output"):
                if key in value:
                    return str(value[key])
        return str(value)
