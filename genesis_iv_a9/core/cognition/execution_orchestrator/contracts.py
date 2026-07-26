from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Iterable, Mapping, Protocol, Tuple

from .enums import (
    DispatchMode,
    ExecutionStatus,
    MissionExecutionStatus,
    ObservationKind,
)
from .errors import InvalidExecutionPlanError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _tuple(values: Iterable[str] | None) -> Tuple[str, ...]:
    return tuple(values or ())


def _freeze_text_mapping(
    value: Mapping[str, str] | None,
) -> Mapping[str, str]:
    return MappingProxyType(dict(sorted((value or {}).items())))


@dataclass(frozen=True, slots=True)
class ActivityExecutionSpec:
    activity_id: str
    title: str
    instruction: str
    expected_result: str
    verification: str
    dispatch_mode: DispatchMode
    dependency_ids: Tuple[str, ...] = field(default_factory=tuple)
    required_capability: str = ""
    rollback_instruction: str = ""
    parameters: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    max_attempts: int = 1
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.activity_id.strip():
            raise InvalidExecutionPlanError("activity_id is required.")
        if not self.instruction.strip():
            raise InvalidExecutionPlanError(
                f"Activity {self.activity_id} requires an instruction."
            )
        if self.max_attempts < 1:
            raise InvalidExecutionPlanError("max_attempts must be at least 1.")
        object.__setattr__(self, "dependency_ids", _tuple(self.dependency_ids))
        object.__setattr__(self, "parameters", _freeze_text_mapping(self.parameters))


@dataclass(frozen=True, slots=True)
class MissionExecutionRequest:
    mission_id: str
    decision_id: str
    activities: Tuple[ActivityExecutionSpec, ...]
    topological_order: Tuple[str, ...]
    policy_id: str = "execution-orchestrator-policy-v1"
    constitution_revision: str = "CONST-0001/1.0"
    request_id: str = ""

    def __post_init__(self) -> None:
        if not self.mission_id.strip() or not self.decision_id.strip():
            raise InvalidExecutionPlanError(
                "mission_id and decision_id are required."
            )
        if not self.activities:
            raise InvalidExecutionPlanError("At least one activity is required.")
        object.__setattr__(self, "activities", tuple(self.activities))
        object.__setattr__(self, "topological_order", tuple(self.topological_order))


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    succeeded: bool
    summary: str
    output_reference: str = ""
    telemetry: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "telemetry", _freeze_text_mapping(self.telemetry))


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    mission_id: str
    decision_id: str
    activity: ActivityExecutionSpec
    attempt: int
    approved: bool


class ActivityExecutor(Protocol):
    capability: str

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...


@dataclass(frozen=True, slots=True)
class ActivityExecutionRecord:
    activity_id: str
    status: ExecutionStatus
    attempt: int
    started_at: str | None = None
    completed_at: str | None = None
    summary: str = ""
    output_reference: str = ""
    error: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionObservation:
    observation_id: str
    mission_id: str
    activity_id: str
    kind: ObservationKind
    message: str
    created_at: str


@dataclass(frozen=True, slots=True)
class MissionExecutionSnapshot:
    execution_id: str
    mission_id: str
    decision_id: str
    status: MissionExecutionStatus
    activities: Tuple[ActivityExecutionRecord, ...]
    observations: Tuple[ExecutionObservation, ...]
    policy_id: str
    constitution_revision: str
    created_at: str
    updated_at: str
