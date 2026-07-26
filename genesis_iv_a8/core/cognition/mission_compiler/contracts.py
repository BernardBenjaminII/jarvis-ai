from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .enums import ActivityExecutionMode, MissionPlanStatus, MissionPriority, NodeKind
from .errors import InvalidMissionSpecificationError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _tuple(values: Iterable[str] | None) -> Tuple[str, ...]:
    return tuple(values or ())


def _freeze_text_mapping(
    value: Mapping[str, str] | None,
) -> Mapping[str, str]:
    return MappingProxyType(dict(sorted((value or {}).items())))


@dataclass(frozen=True, slots=True)
class ObjectiveSpecification:
    key: str
    title: str
    description: str
    success_criteria: Tuple[str, ...]
    priority: int = 100
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise InvalidMissionSpecificationError("Objective key is required.")
        if not self.success_criteria:
            raise InvalidMissionSpecificationError(
                f"Objective {self.key} requires success criteria."
            )
        object.__setattr__(self, "success_criteria", _tuple(self.success_criteria))
        object.__setattr__(self, "depends_on", _tuple(self.depends_on))


@dataclass(frozen=True, slots=True)
class TaskSpecification:
    key: str
    objective_key: str
    title: str
    description: str
    verification: str
    required_capabilities: Tuple[str, ...] = field(default_factory=tuple)
    required_resources: Tuple[str, ...] = field(default_factory=tuple)
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    estimated_minutes: int | None = None

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.objective_key.strip():
            raise InvalidMissionSpecificationError(
                "Task key and objective_key are required."
            )
        if not self.verification.strip():
            raise InvalidMissionSpecificationError(
                f"Task {self.key} requires a verification condition."
            )
        if self.estimated_minutes is not None and self.estimated_minutes < 0:
            raise InvalidMissionSpecificationError(
                "estimated_minutes must be non-negative."
            )
        object.__setattr__(
            self, "required_capabilities", _tuple(self.required_capabilities)
        )
        object.__setattr__(
            self, "required_resources", _tuple(self.required_resources)
        )
        object.__setattr__(self, "depends_on", _tuple(self.depends_on))


@dataclass(frozen=True, slots=True)
class ActivitySpecification:
    key: str
    task_key: str
    title: str
    instruction: str
    expected_result: str
    verification: str
    execution_mode: ActivityExecutionMode = ActivityExecutionMode.HUMAN
    required_capability: str = ""
    rollback: str = ""
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    parameters: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.task_key.strip():
            raise InvalidMissionSpecificationError(
                "Activity key and task_key are required."
            )
        if not self.instruction.strip():
            raise InvalidMissionSpecificationError(
                f"Activity {self.key} requires an instruction."
            )
        object.__setattr__(self, "depends_on", _tuple(self.depends_on))
        object.__setattr__(self, "parameters", _freeze_text_mapping(self.parameters))


@dataclass(frozen=True, slots=True)
class MissionCompilationRequest:
    decision_id: str
    mission_title: str
    mission_intent: str
    selected_coa_id: str
    decision_approved: bool
    objectives: Tuple[ObjectiveSpecification, ...]
    tasks: Tuple[TaskSpecification, ...]
    activities: Tuple[ActivitySpecification, ...]
    priority: MissionPriority = MissionPriority.NORMAL
    constraints: Tuple[str, ...] = field(default_factory=tuple)
    required_resources: Tuple[str, ...] = field(default_factory=tuple)
    policy_id: str = "mission-compiler-policy-v1"
    constitution_revision: str = "CONST-0001/1.0"
    situation_reference: str = ""
    reasoning_reference: str = ""
    observation_ids: Tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    hypothesis_ids: Tuple[str, ...] = field(default_factory=tuple)
    request_id: str = ""

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise InvalidMissionSpecificationError("decision_id is required.")
        if not self.selected_coa_id.strip():
            raise InvalidMissionSpecificationError("selected_coa_id is required.")
        if not self.mission_title.strip() or not self.mission_intent.strip():
            raise InvalidMissionSpecificationError(
                "mission_title and mission_intent are required."
            )
        if not self.objectives or not self.tasks or not self.activities:
            raise InvalidMissionSpecificationError(
                "A mission requires objectives, tasks, and activities."
            )
        for name in (
            "objectives",
            "tasks",
            "activities",
            "constraints",
            "required_resources",
            "observation_ids",
            "evidence_ids",
            "hypothesis_ids",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class Objective:
    objective_id: str
    mission_id: str
    key: str
    title: str
    description: str
    success_criteria: Tuple[str, ...]
    priority: int
    dependency_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Task:
    task_id: str
    mission_id: str
    objective_id: str
    key: str
    title: str
    description: str
    verification: str
    required_capabilities: Tuple[str, ...]
    required_resources: Tuple[str, ...]
    dependency_ids: Tuple[str, ...]
    estimated_minutes: int | None


@dataclass(frozen=True, slots=True)
class Activity:
    activity_id: str
    mission_id: str
    task_id: str
    key: str
    title: str
    instruction: str
    expected_result: str
    verification: str
    execution_mode: ActivityExecutionMode
    required_capability: str
    rollback: str
    dependency_ids: Tuple[str, ...]
    parameters: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", _freeze_text_mapping(self.parameters))


@dataclass(frozen=True, slots=True)
class ExecutionNode:
    node_id: str
    kind: NodeKind
    dependency_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutionGraph:
    nodes: Tuple[ExecutionNode, ...]
    topological_order: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MissionTrace:
    decision_id: str
    selected_coa_id: str
    policy_id: str
    constitution_revision: str
    situation_reference: str
    reasoning_reference: str
    observation_ids: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    hypothesis_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MissionPlan:
    mission_id: str
    decision_id: str
    selected_coa_id: str
    title: str
    intent: str
    status: MissionPlanStatus
    priority: MissionPriority
    objectives: Tuple[Objective, ...]
    tasks: Tuple[Task, ...]
    activities: Tuple[Activity, ...]
    execution_graph: ExecutionGraph
    constraints: Tuple[str, ...]
    required_resources: Tuple[str, ...]
    trace: MissionTrace
    policy_id: str
    constitution_revision: str
    created_at: str
