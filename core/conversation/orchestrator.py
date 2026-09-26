"""Executive conversation orchestration with C-4 knowledge grounding."""
from __future__ import annotations

from dataclasses import dataclass
from copy import copy
from time import perf_counter
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
        creative_handler: SynthesisHandler | None = None,
    ) -> None:
        self.director = director
        self.synthesis_handler = synthesis_handler
        self.grounding_service = grounding_service
        self.awareness_service = awareness_service
        self.observability_service = observability_service
        self.creative_handler = creative_handler

    def execute(self, context: ExecutiveRequestContext) -> OrchestrationResult:
        # The API owns one orchestrator. Mutable answer plans belong to a request,
        # not to that process-wide instance. Services remain shared as before.
        worker = copy(self)
        for name in ("_last_grounded_answer_plan", "_last_grounded_answer_response",
                     "_last_grounded_answer_telemetry", "_grounded_answer_output_fallback"):
            setattr(worker, name, None)
        return worker._execute_request(context)

    def _execute_request(self, context: ExecutiveRequestContext) -> OrchestrationResult:
        # GENESIS_PERFORMANCE_R1
        perf_started = perf_counter()
        perf_trace = {
            "grounding_ms": None,
            "synthesis_preparation_ms": None,
            "primary_llm_ms": None,
            "primary_validation_ms": None,
            "repair_prompt_ms": None,
            "repair_llm_ms": None,
            "repair_validation_ms": None,
            "orchestration_total_ms": None,
        }

        from core.conversation.request_routing import request_route, runtime_answer
        route = request_route(context.operator_input)
        if route == "runtime":
            from core.src.cognition.platform_status import snapshot
            state = snapshot()
            return self._direct_result(runtime_answer(state), route, {"runtime": state})
        if route in {"creative", "social"} and self.creative_handler is not None:
            answer = self._normalize_answer(self.creative_handler(context.operator_input))
            if not answer.strip() or "[LLM ERROR]" in answer:
                raise RuntimeError("Creative generation failed; check the local model service.")
            return self._direct_result(answer, route, {"source_kind": "generated_text"})
        if route == "disk_command":
            from core.src.cognition.platform_status import snapshot
            from core.conversation.command_documentation import disk_command_answer
            from core.conversation.bounded_catalog import bounded_command_grounding
            grounding, search_status = bounded_command_grounding(self.grounding_service, context)
            result = disk_command_answer(grounding, snapshot())
            result["technical_details"]["catalog_search"] = search_status
            if search_status["status"] == "timeout":
                result["answer"] += "\n\nThe catalog search timed out; it did not establish whether relevant material exists."
            return self._direct_result(result["answer"], route, result["technical_details"])
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
            _perf_stage = perf_counter()
            grounding = self.grounding_service.ground(context)
            perf_trace["grounding_ms"] = round(
                (perf_counter() - _perf_stage) * 1000.0, 2
            )

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
        _perf_stage = perf_counter()
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
        perf_trace["synthesis_preparation_ms"] = round(
            (perf_counter() - _perf_stage) * 1000.0, 2
        )

        grounded_plan = getattr(self, "_last_grounded_answer_plan", None)
        grounded_state = str(
            getattr(getattr(grounded_plan, "state", None), "value", "")
        ).casefold()
        _perf_stage = perf_counter()
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
        perf_trace["primary_llm_ms"] = round(
            (perf_counter() - _perf_stage) * 1000.0, 2
        )

        technical_details = None

        if isinstance(synthesis_result, dict):
            technical_details = synthesis_result.get("technical_details")

        answer = self._normalize_answer(synthesis_result)

        # GENESIS_GROUNDED_OUTPUT_DIAGNOSTIC_R1
        # Preserve the model response before grounded-output enforcement.
        # Diagnostic only: this does not alter validation or user-visible output.
        self._grounded_answer_pre_enforcement = answer
        self._grounded_answer_output_reason = None

        if knowledge_state is not None:
            from core.conversation.grounded_answer.integration import (
                build_grounded_answer_repair_prompt,
                enforce_grounded_answer_output,
            )

            primary_answer = answer
            _perf_stage = perf_counter()
            answer = enforce_grounded_answer_output(
                self,
                primary_answer,
            )
            perf_trace["primary_validation_ms"] = round(
                (perf_counter() - _perf_stage) * 1000.0, 2
            )

            primary_failed = bool(
                getattr(
                    self,
                    "_grounded_answer_output_fallback",
                    False,
                )
            )

            self._grounded_answer_repair_attempted = False
            self._grounded_answer_repair_input = None
            self._grounded_answer_repair_output = None
            self._grounded_answer_repair_reason = None
            self._grounded_answer_repair_detail = None
            self._grounded_answer_repair_accepted = None
            self._grounded_answer_primary_failure_reason = None
            self._grounded_answer_primary_failure_detail = None

            # One constrained repair attempt is permitted when qualified
            # evidence exists but the primary model answer fails grounded
            # output validation. The same validators are then applied again.
            if primary_failed and grounded_state != "unknown":
                _perf_stage = perf_counter()
                repair_prompt = build_grounded_answer_repair_prompt(
                    self,
                    primary_answer,
                )
                perf_trace["repair_prompt_ms"] = round(
                    (perf_counter() - _perf_stage) * 1000.0, 2
                )

                if repair_prompt:
                    primary_failure_reason = getattr(
                        self,
                        "_grounded_answer_output_reason",
                        None,
                    )
                    primary_failure_detail = getattr(
                        self,
                        "_grounded_answer_output_detail",
                        None,
                    )

                    self._grounded_answer_repair_attempted = True
                    self._grounded_answer_repair_input = repair_prompt

                    _perf_stage = perf_counter()
                    repair_result = self.synthesis_handler(
                        repair_prompt
                    )
                    perf_trace["repair_llm_ms"] = round(
                        (perf_counter() - _perf_stage) * 1000.0, 2
                    )
                    repair_answer = self._normalize_answer(
                        repair_result
                    )

                    self._grounded_answer_repair_output = (
                        repair_answer
                    )

                    _perf_stage = perf_counter()
                    answer = enforce_grounded_answer_output(
                        self,
                        repair_answer,
                    )
                    perf_trace["repair_validation_ms"] = round(
                        (perf_counter() - _perf_stage) * 1000.0, 2
                    )

                    repair_failed = bool(
                        getattr(
                            self,
                            "_grounded_answer_output_fallback",
                            False,
                        )
                    )

                    self._grounded_answer_repair_accepted = (
                        not repair_failed
                    )
                    self._grounded_answer_repair_detail = getattr(
                        self,
                        "_grounded_answer_output_detail",
                        None,
                    )

                    if repair_failed:
                        self._grounded_answer_repair_reason = (
                            getattr(
                                self,
                                "_grounded_answer_output_reason",
                                None,
                            )
                        )
                    else:
                        self._grounded_answer_repair_reason = None

                    # Preserve the original failure separately for
                    # request-local diagnostics.
                    self._grounded_answer_primary_failure_reason = (
                        primary_failure_reason
                    )
                    self._grounded_answer_primary_failure_detail = (
                        primary_failure_detail
                    )

        # GENESIS_GROUNDED_OUTPUT_DIAGNOSTIC_R2
        # Transport request-local synthesis/validation diagnostics with the
        # result. The orchestrator executes on a request-local worker copy,
        # so these values must not be read from the process-wide instance.
        if technical_details is None:
            technical_details = {}
        elif not isinstance(technical_details, dict):
            technical_details = {
                "synthesis_technical_details": technical_details,
            }
        else:
            technical_details = dict(technical_details)

        perf_trace["orchestration_total_ms"] = round(
            (perf_counter() - perf_started) * 1000.0, 2
        )
        technical_details["performance_r1"] = perf_trace

        technical_details["grounded_output_diagnostic"] = {
            "pre_enforcement_answer": getattr(
                self,
                "_grounded_answer_pre_enforcement",
                None,
            ),
            "fallback": getattr(
                self,
                "_grounded_answer_output_fallback",
                None,
            ),
            "reason": getattr(
                self,
                "_grounded_answer_output_reason",
                None,
            ),
            "plan_state": str(
                getattr(
                    getattr(
                        getattr(self, "_last_grounded_answer_plan", None),
                        "state",
                        None,
                    ),
                    "value",
                    getattr(
                        getattr(
                            getattr(self, "_last_grounded_answer_plan", None),
                            "state",
                            None,
                        ),
                        "value",
                        "",
                    ),
                )
            ),
            "citation_ids": [
                getattr(citation, "citation_id", None)
                for citation in (
                    getattr(
                        getattr(self, "_last_grounded_answer_plan", None),
                        "citations",
                        (),
                    )
                    or ()
                )
            ],
            "primary_failure_reason": getattr(
                self,
                "_grounded_answer_primary_failure_reason",
                None,
            ),
            "primary_failure_detail": getattr(
                self,
                "_grounded_answer_primary_failure_detail",
                None,
            ),
            "repair": {
                "attempted": getattr(
                    self,
                    "_grounded_answer_repair_attempted",
                    False,
                ),
                "accepted": getattr(
                    self,
                    "_grounded_answer_repair_accepted",
                    None,
                ),
                "reason": getattr(
                    self,
                    "_grounded_answer_repair_reason",
                    None,
                ),
                "detail": getattr(
                    self,
                    "_grounded_answer_repair_detail",
                    None,
                ),
                "output": getattr(
                    self,
                    "_grounded_answer_repair_output",
                    None,
                ),
            },
        }

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
    def _direct_result(answer, route, details):
        return OrchestrationResult(
            answer=answer, assignments=(),
            trace=(ConversationTraceEvent(
                stage="request.routed", status="completed",
                detail=f"Request handled through the {route} route.",
                data={"route": route, "source_kind": details.get("source_kind", route)},
            ),),
            technical_details={"request_route": route, **details},
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
