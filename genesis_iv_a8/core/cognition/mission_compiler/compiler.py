from __future__ import annotations

import hashlib
import json
from types import MappingProxyType

from .contracts import (
    Activity,
    ExecutionNode,
    MissionCompilationRequest,
    MissionPlan,
    MissionTrace,
    Objective,
    Task,
    utc_now_iso,
)
from .enums import MissionPlanStatus, NodeKind
from .errors import (
    DecisionNotApprovedError,
    InvalidMissionSpecificationError,
    OrphanPlanNodeError,
)
from .graph import build_execution_graph


def _stable_id(prefix: str, *parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:20]}"


class ExecutiveMissionCompiler:
    """Compile an approved Executive Decision into a deterministic Mission Plan."""

    def compile(self, request: MissionCompilationRequest) -> MissionPlan:
        if not request.decision_approved:
            raise DecisionNotApprovedError(
                "Only an approved Executive Decision may be compiled."
            )

        self._validate_unique_keys(request)

        mission_id = _stable_id(
            "mission",
            request.decision_id,
            request.selected_coa_id,
            request.request_id,
            request.mission_title,
        )

        objective_ids = {
            spec.key: _stable_id("objective", mission_id, spec.key)
            for spec in request.objectives
        }
        task_ids = {
            spec.key: _stable_id("task", mission_id, spec.key)
            for spec in request.tasks
        }
        activity_ids = {
            spec.key: _stable_id("activity", mission_id, spec.key)
            for spec in request.activities
        }

        objectives = self._compile_objectives(
            request, mission_id, objective_ids
        )
        tasks = self._compile_tasks(
            request, mission_id, objective_ids, task_ids
        )
        activities = self._compile_activities(
            request, mission_id, task_ids, activity_ids
        )

        nodes: list[ExecutionNode] = []
        nodes.extend(
            ExecutionNode(
                node_id=item.objective_id,
                kind=NodeKind.OBJECTIVE,
                dependency_ids=item.dependency_ids,
            )
            for item in objectives
        )
        nodes.extend(
            ExecutionNode(
                node_id=item.task_id,
                kind=NodeKind.TASK,
                dependency_ids=(item.objective_id,) + item.dependency_ids,
            )
            for item in tasks
        )
        nodes.extend(
            ExecutionNode(
                node_id=item.activity_id,
                kind=NodeKind.ACTIVITY,
                dependency_ids=(item.task_id,) + item.dependency_ids,
            )
            for item in activities
        )

        graph = build_execution_graph(nodes)

        trace = MissionTrace(
            decision_id=request.decision_id,
            selected_coa_id=request.selected_coa_id,
            policy_id=request.policy_id,
            constitution_revision=request.constitution_revision,
            situation_reference=request.situation_reference,
            reasoning_reference=request.reasoning_reference,
            observation_ids=tuple(sorted(set(request.observation_ids))),
            evidence_ids=tuple(sorted(set(request.evidence_ids))),
            hypothesis_ids=tuple(sorted(set(request.hypothesis_ids))),
        )

        return MissionPlan(
            mission_id=mission_id,
            decision_id=request.decision_id,
            selected_coa_id=request.selected_coa_id,
            title=request.mission_title,
            intent=request.mission_intent,
            status=MissionPlanStatus.COMPILED,
            priority=request.priority,
            objectives=objectives,
            tasks=tasks,
            activities=activities,
            execution_graph=graph,
            constraints=tuple(request.constraints),
            required_resources=tuple(request.required_resources),
            trace=trace,
            policy_id=request.policy_id,
            constitution_revision=request.constitution_revision,
            created_at=utc_now_iso(),
        )

    def _validate_unique_keys(self, request: MissionCompilationRequest) -> None:
        for label, values in (
            ("objective", [item.key for item in request.objectives]),
            ("task", [item.key for item in request.tasks]),
            ("activity", [item.key for item in request.activities]),
        ):
            if len(values) != len(set(values)):
                raise InvalidMissionSpecificationError(
                    f"Duplicate {label} keys are not permitted."
                )

    def _compile_objectives(
        self,
        request: MissionCompilationRequest,
        mission_id: str,
        objective_ids: dict[str, str],
    ) -> tuple[Objective, ...]:
        objectives: list[Objective] = []
        for spec in sorted(request.objectives, key=lambda item: (item.priority, item.key)):
            try:
                dependencies = tuple(
                    objective_ids[key] for key in spec.depends_on
                )
            except KeyError as exc:
                raise OrphanPlanNodeError(
                    f"Objective {spec.key} depends on unknown objective {exc.args[0]}."
                ) from exc

            objectives.append(
                Objective(
                    objective_id=objective_ids[spec.key],
                    mission_id=mission_id,
                    key=spec.key,
                    title=spec.title,
                    description=spec.description,
                    success_criteria=tuple(spec.success_criteria),
                    priority=spec.priority,
                    dependency_ids=dependencies,
                )
            )
        return tuple(objectives)

    def _compile_tasks(
        self,
        request: MissionCompilationRequest,
        mission_id: str,
        objective_ids: dict[str, str],
        task_ids: dict[str, str],
    ) -> tuple[Task, ...]:
        tasks: list[Task] = []
        for spec in sorted(request.tasks, key=lambda item: item.key):
            if spec.objective_key not in objective_ids:
                raise OrphanPlanNodeError(
                    f"Task {spec.key} references unknown objective "
                    f"{spec.objective_key}."
                )
            try:
                dependencies = tuple(task_ids[key] for key in spec.depends_on)
            except KeyError as exc:
                raise OrphanPlanNodeError(
                    f"Task {spec.key} depends on unknown task {exc.args[0]}."
                ) from exc

            tasks.append(
                Task(
                    task_id=task_ids[spec.key],
                    mission_id=mission_id,
                    objective_id=objective_ids[spec.objective_key],
                    key=spec.key,
                    title=spec.title,
                    description=spec.description,
                    verification=spec.verification,
                    required_capabilities=tuple(spec.required_capabilities),
                    required_resources=tuple(spec.required_resources),
                    dependency_ids=dependencies,
                    estimated_minutes=spec.estimated_minutes,
                )
            )
        return tuple(tasks)

    def _compile_activities(
        self,
        request: MissionCompilationRequest,
        mission_id: str,
        task_ids: dict[str, str],
        activity_ids: dict[str, str],
    ) -> tuple[Activity, ...]:
        activities: list[Activity] = []
        for spec in sorted(request.activities, key=lambda item: item.key):
            if spec.task_key not in task_ids:
                raise OrphanPlanNodeError(
                    f"Activity {spec.key} references unknown task {spec.task_key}."
                )
            try:
                dependencies = tuple(
                    activity_ids[key] for key in spec.depends_on
                )
            except KeyError as exc:
                raise OrphanPlanNodeError(
                    f"Activity {spec.key} depends on unknown activity "
                    f"{exc.args[0]}."
                ) from exc

            activities.append(
                Activity(
                    activity_id=activity_ids[spec.key],
                    mission_id=mission_id,
                    task_id=task_ids[spec.task_key],
                    key=spec.key,
                    title=spec.title,
                    instruction=spec.instruction,
                    expected_result=spec.expected_result,
                    verification=spec.verification,
                    execution_mode=spec.execution_mode,
                    required_capability=spec.required_capability,
                    rollback=spec.rollback,
                    dependency_ids=dependencies,
                    parameters=MappingProxyType(dict(spec.parameters)),
                )
            )
        return tuple(activities)
