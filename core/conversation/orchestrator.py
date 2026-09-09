"""Executive conversation orchestration with C-4 knowledge grounding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.conversation.contracts import ConversationTraceEvent, ExecutiveRequestContext
from core.conversation.grounding import CatalogGroundingService, GroundingResult
from core.executive.director import ExecutiveDirector
from core.executive.models import Mission
from core.knowledge_awareness import ExecutiveKnowledgeAwarenessService, ExecutiveKnowledgeState
from core.observability import ExecutiveObservabilityService, MissionTransparencySnapshot

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
    knowledge_state: ExecutiveKnowledgeState | None = None
    transparency: MissionTransparencySnapshot | None = None
    technical_details: Any | None = None

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
        if self.knowledge_state is not None:
            metadata["executive_knowledge_state"] = self.knowledge_state.to_dict()
            metadata["knowledge_awareness"] = "executive_evidence_reasoning"
        if self.transparency is not None:
            metadata["mission_transparency"] = self.transparency.to_dict()
            metadata["observability"] = "executive_mission_transparency"
        if self.technical_details is not None:
            metadata["technical_details"] = self.technical_details
        return metadata


class ExecutiveConversationOrchestrator:
    """Ground, delegate, execute, and synthesize each operator request."""

    def __init__(
        self,
        *,
        director: ExecutiveDirector,
        synthesis_handler: SynthesisHandler,
        grounding_service: CatalogGroundingService | None = None,
        awareness_service: ExecutiveKnowledgeAwarenessService | None = None,
        observability_service: ExecutiveObservabilityService | None = None,
    ) -> None:
        self.director = director
        self.synthesis_handler = synthesis_handler
        self.grounding_service = grounding_service
        self.awareness_service = awareness_service
        self.observability_service = observability_service

    def execute(self, context: ExecutiveRequestContext) -> OrchestrationResult:
        from core.conversation.catalog_status import (
            catalog_status_request,
            catalog_topic_request,
            inspect_catalog,
            inspect_catalog_topic,
            render_catalog_status,
            render_catalog_topic,
        )
        from core.conversation.filename_lookup import filename_request, lookup_filename, render_lookup

        catalog_topic = catalog_topic_request(context.operator_input)
        if catalog_topic is not None and self.grounding_service is not None:
            inventory = inspect_catalog_topic(self.grounding_service.database_path, catalog_topic)
            return OrchestrationResult(
                answer=render_catalog_topic(inventory), assignments=(),
                trace=(ConversationTraceEvent(
                    stage="knowledge.catalog_inventory",
                    status="completed" if inventory["status"] != "unavailable" else "gap",
                    detail="Read-only catalog metadata lookup; passage retrieval bypassed.",
                    data=inventory,
                ),),
                technical_details={"catalog_inventory": inventory},
            )

        if catalog_status_request(context.operator_input) and self.grounding_service is not None:
            inspection = inspect_catalog(self.grounding_service.database_path)
            return OrchestrationResult(
                answer=render_catalog_status(inspection),
                assignments=(),
                trace=(ConversationTraceEvent(
                    stage="knowledge.catalog_status",
                    status="completed" if inspection["status"] == "available" else "gap",
                    detail="Read-only deterministic catalog inspection; document retrieval bypassed.",
                    data=inspection,
                ),),
                technical_details={"catalog_status": inspection},
            )

        filename = filename_request(context.operator_input)
        if filename is not None and self.grounding_service is not None:
            lookup = lookup_filename(self.grounding_service.database_path, filename)
            return OrchestrationResult(
                answer=render_lookup(lookup), assignments=(),
                trace=(ConversationTraceEvent(
                    stage="knowledge.filename_lookup",
                    status="completed" if lookup["status"] != "unavailable" else "gap",
                    detail="Read-only exact filename lookup.", data=lookup,
                ),),
                technical_details={"filename_lookup": lookup},
            )

        trace: list[ConversationTraceEvent] = []
        assignments: list[DirectorAssignment] = []
        grounding: GroundingResult | None = None
        knowledge_state: ExecutiveKnowledgeState | None = None
        grounding_qualification: Any | None = None

        if self.grounding_service is not None:
            trace.append(ConversationTraceEvent(
                stage="knowledge.grounding",
                status="processing",
                detail="Searching the canonical knowledge catalog for objective evidence.",
            ))
            grounding = self.grounding_service.ground(context)

            # Snapshot the qualification produced by this request before
            # director execution can perform another catalog search and
            # replace the ContextVar's current value.
            from core.knowledge_catalog.qualified_search import (
                get_last_qualification_result,
            )

            grounding_qualification = get_last_qualification_result()

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
            if self.awareness_service is not None:
                trace.append(ConversationTraceEvent(
                    stage="knowledge.awareness", status="processing",
                    detail="Assessing catalog coverage, evidence, contradictions, and answerability.",
                ))
                knowledge_state = self.awareness_service.assess(grounding)
                trace.append(ConversationTraceEvent(
                    stage="knowledge.awareness", status="completed",
                    detail=(f"Knowledge state is {knowledge_state.status}; "
                            f"answerability is {knowledge_state.answerability}."),
                    data={"confidence":knowledge_state.confidence,
                          "research_queue_count":len(knowledge_state.research_queue),
                          "contradiction_count":knowledge_state.contradiction_count},
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
        synthesis_input = context.operator_input
        if grounding is not None:
            synthesis_input = grounding.synthesis_input(synthesis_input)
        if knowledge_state is not None:
            synthesis_input = knowledge_state.synthesis_input(synthesis_input)

            from core.conversation.grounded_answer.integration import (
                augment_synthesis_input,
            )

            synthesis_input = augment_synthesis_input(
                self,
                context,
                synthesis_input,
                qualification=grounding_qualification,
            )
        grounded_plan = getattr(self, "_last_grounded_answer_plan", None)
        grounded_state = str(
            getattr(getattr(grounded_plan, "state", None), "value", "")
        ).casefold()
        if grounded_plan is not None and grounded_state == "unknown":
            # Fail closed before the model is invoked.  UNKNOWN means there is
            # no qualified basis for synthesis; model knowledge and web-style
            # citations must not be substituted for catalog evidence.
            from core.conversation.grounded_answer.integration import (
                ensure_grounded_answer_service,
            )

            synthesis_result = ensure_grounded_answer_service(
                self
            ).engine.deterministic_answer(grounded_plan)
        else:
            synthesis_result = self.synthesis_handler(synthesis_input)
        technical_details = None

        if isinstance(synthesis_result, dict):
            technical_details = synthesis_result.get("technical_details")

        answer = self._normalize_answer(synthesis_result)

        if knowledge_state is not None:
            from core.conversation.grounded_answer.integration import (
                enforce_grounded_answer_output,
            )

            answer = enforce_grounded_answer_output(self, answer)

        trace.append(ConversationTraceEvent(
            stage="executive.synthesis",
            status="completed",
            detail="Unified JARVIS response completed.",
        ))
        provisional = OrchestrationResult(
            answer=answer,
            assignments=tuple(assignments),
            trace=tuple(trace),
            grounding=grounding,
            knowledge_state=knowledge_state,
            technical_details=technical_details,
        )
        transparency = (
            None
            if self.observability_service is None
            else self.observability_service.project(context=context, result=provisional)
        )
        return OrchestrationResult(
            answer=answer,
            assignments=tuple(assignments),
            trace=tuple(trace),
            grounding=grounding,
            knowledge_state=knowledge_state,
            transparency=transparency,
            technical_details=technical_details,
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
