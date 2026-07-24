"""Canonical immutable planning contracts for JARVIS.

The contracts in this module describe plan data. They do not perform execution,
authorization, or autonomous mission control.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import uuid4

from core.executive.planning.enums import (
    AuthorizationMode,
    ConstraintKind,
    DependencyType,
    MissionPriority,
    PlanElementKind,
    PlanState,
    ResourceKind,
    RiskLevel,
    RiskStatus,
)


def new_identifier(prefix: str) -> str:
    """Return a sortable, human-readable unique identifier."""

    return f"{prefix}_{uuid4().hex}"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def _normalize_json_value(value: Any) -> Any:
    """Convert model values into deterministic JSON-compatible values."""

    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()

    if hasattr(value, "value"):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }

    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]

    return value


@dataclass(frozen=True, slots=True)
class AuthorizationRequirement:
    """Authorization required for a plan element."""

    mode: AuthorizationMode
    approving_authority: str | None = None
    inherited_from_parent: bool = False
    expires_at: datetime | None = None
    conditions: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.mode
            in {
                AuthorizationMode.COMMANDER_APPROVAL,
                AuthorizationMode.DELEGATED_APPROVAL,
                AuthorizationMode.POLICY_APPROVAL,
            }
            and not self.approving_authority
        ):
            raise ValueError(
                f"{self.mode.value} requires an approving_authority"
            )


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Reference to evidence or knowledge used during planning."""

    reference_id: str
    source: str
    claim: str
    confidence: float = 1.0
    retrieved_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Assumption:
    """A claim temporarily treated as true for planning purposes."""

    assumption_id: str
    description: str
    confidence: float
    rationale: str
    validation_method: str
    impact_if_false: str
    blocking: bool = False
    expires_at: datetime | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Assumption description cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Assumption confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Constraint:
    """A bounded condition within which planning must operate."""

    constraint_id: str
    kind: ConstraintKind
    description: str
    mandatory: bool = True
    source: str | None = None
    validation_rule: str | None = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Constraint description cannot be empty")


@dataclass(frozen=True, slots=True)
class ResourceRequirement:
    """Resource required by a plan element."""

    resource_id: str
    kind: ResourceKind
    name: str
    quantity: float = 1.0
    unit: str = "unit"
    required: bool = True
    exclusive: bool = False
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("Resource quantity cannot be negative")

        if not self.name.strip():
            raise ValueError("Resource name cannot be empty")


@dataclass(frozen=True, slots=True)
class Risk:
    """Risk associated with a mission or plan element."""

    risk_id: str
    title: str
    description: str
    likelihood: RiskLevel
    impact: RiskLevel
    status: RiskStatus = RiskStatus.IDENTIFIED
    owner: str | None = None
    mitigation: str | None = None
    contingency: str | None = None
    trigger_conditions: tuple[str, ...] = ()
    affected_element_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Risk title cannot be empty")

        if not self.description.strip():
            raise ValueError("Risk description cannot be empty")


@dataclass(frozen=True, slots=True)
class Dependency:
    """Directed dependency from one plan element to another.

    ``predecessor_id`` identifies the element that must satisfy the dependency.
    ``successor_id`` identifies the dependent element.
    """

    dependency_id: str
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    required: bool = True
    description: str | None = None
    lag_seconds: int = 0

    def __post_init__(self) -> None:
        if self.predecessor_id == self.successor_id:
            raise ValueError("A plan element cannot depend on itself")

        if self.lag_seconds < 0:
            raise ValueError("Dependency lag cannot be negative")


@dataclass(frozen=True, slots=True)
class Command:
    """Lowest canonical executable unit in a mission plan."""

    command_id: str
    activity_id: str
    name: str
    description: str
    capability: str
    operation: str
    authorization: AuthorizationRequirement
    parameters: Mapping[str, Any] = field(default_factory=dict)
    expected_output: str | None = None
    timeout_seconds: int | None = None
    retry_limit: int = 0
    reversible: bool = False
    rollback_operation: str | None = None
    completion_criteria: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    risks: tuple[Risk, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def element_id(self) -> str:
        return self.command_id

    @property
    def element_kind(self) -> PlanElementKind:
        return PlanElementKind.COMMAND

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Command name cannot be empty")

        if not self.capability.strip():
            raise ValueError("Command capability cannot be empty")

        if not self.operation.strip():
            raise ValueError("Command operation cannot be empty")

        if self.retry_limit < 0:
            raise ValueError("Command retry_limit cannot be negative")

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("Command timeout_seconds must be positive")

        if self.rollback_operation and not self.reversible:
            raise ValueError(
                "rollback_operation requires command reversible=True"
            )


@dataclass(frozen=True, slots=True)
class Activity:
    """Operational step contained by a task."""

    activity_id: str
    task_id: str
    name: str
    description: str
    authorization: AuthorizationRequirement
    commands: tuple[Command, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    risks: tuple[Risk, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def element_id(self) -> str:
        return self.activity_id

    @property
    def element_kind(self) -> PlanElementKind:
        return PlanElementKind.ACTIVITY

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Activity name cannot be empty")


@dataclass(frozen=True, slots=True)
class Task:
    """Bounded unit of work that contributes to an objective."""

    task_id: str
    objective_id: str
    name: str
    description: str
    expected_output: str
    authorization: AuthorizationRequirement
    activities: tuple[Activity, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    risks: tuple[Risk, ...] = ()
    responsible_capability: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def element_id(self) -> str:
        return self.task_id

    @property
    def element_kind(self) -> PlanElementKind:
        return PlanElementKind.TASK

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Task name cannot be empty")

        if not self.expected_output.strip():
            raise ValueError("Task expected_output cannot be empty")

        if not self.completion_criteria:
            raise ValueError("Task must define completion criteria")


@dataclass(frozen=True, slots=True)
class Objective:
    """Measurable result required to satisfy mission intent."""

    objective_id: str
    mission_id: str
    name: str
    description: str
    desired_outcome: str
    tasks: tuple[Task, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    risks: tuple[Risk, ...] = ()
    priority: MissionPriority = MissionPriority.NORMAL
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def element_id(self) -> str:
        return self.objective_id

    @property
    def element_kind(self) -> PlanElementKind:
        return PlanElementKind.OBJECTIVE

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Objective name cannot be empty")

        if not self.desired_outcome.strip():
            raise ValueError("Objective desired_outcome cannot be empty")

        if not self.completion_criteria:
            raise ValueError("Objective must define completion criteria")


@dataclass(frozen=True, slots=True)
class Mission:
    """Highest operational unit controlled by the executive architecture."""

    mission_id: str
    title: str
    commander_intent: str
    desired_end_state: str
    owner: str
    objectives: tuple[Objective, ...] = ()
    priority: MissionPriority = MissionPriority.NORMAL
    constraints: tuple[Constraint, ...] = ()
    prohibitions: tuple[str, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    risks: tuple[Risk, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    authorization: AuthorizationRequirement = field(
        default_factory=lambda: AuthorizationRequirement(
            mode=AuthorizationMode.COMMANDER_APPROVAL,
            approving_authority="commander",
        )
    )
    created_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def element_id(self) -> str:
        return self.mission_id

    @property
    def element_kind(self) -> PlanElementKind:
        return PlanElementKind.MISSION

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Mission title cannot be empty")

        if not self.commander_intent.strip():
            raise ValueError("Mission commander_intent cannot be empty")

        if not self.desired_end_state.strip():
            raise ValueError("Mission desired_end_state cannot be empty")

        if not self.owner.strip():
            raise ValueError("Mission owner cannot be empty")

        if not self.completion_criteria:
            raise ValueError("Mission must define completion criteria")


@dataclass(frozen=True, slots=True)
class PlanVersion:
    """Immutable historical version of a mission plan."""

    plan_id: str
    version: int
    mission: Mission
    state: PlanState
    dependencies: tuple[Dependency, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    created_by: str = "planning_director"
    parent_version: int | None = None
    revision_reason: str | None = None
    notes: tuple[str, ...] = ()
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("Plan version must be at least 1")

        if self.parent_version is not None:
            if self.parent_version < 1:
                raise ValueError("Parent version must be at least 1")

            if self.parent_version >= self.version:
                raise ValueError(
                    "Parent version must be lower than the current version"
                )

        calculated = self.calculate_fingerprint()

        if self.fingerprint and self.fingerprint != calculated:
            raise ValueError(
                "Provided plan fingerprint does not match plan contents"
            )

        object.__setattr__(self, "fingerprint", calculated)

    def canonical_payload(self) -> dict[str, Any]:
        """Return the deterministic plan representation used for hashing."""

        payload = asdict(self)
        payload.pop("fingerprint", None)
        return _normalize_json_value(payload)

    def calculate_fingerprint(self) -> str:
        """Calculate the immutable SHA-256 fingerprint for this version."""

        encoded = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the version."""

        payload = self.canonical_payload()
        payload["fingerprint"] = self.fingerprint
        return payload


@dataclass(frozen=True, slots=True)
class MissionPlan:
    """Plan aggregate containing immutable historical versions."""

    plan_id: str
    versions: tuple[PlanVersion, ...]

    def __post_init__(self) -> None:
        if not self.versions:
            raise ValueError("MissionPlan must contain at least one version")

        expected_versions = list(range(1, len(self.versions) + 1))
        actual_versions = [version.version for version in self.versions]

        if actual_versions != expected_versions:
            raise ValueError(
                "MissionPlan versions must be contiguous and ordered from 1"
            )

        if any(version.plan_id != self.plan_id for version in self.versions):
            raise ValueError(
                "All PlanVersion records must reference the MissionPlan plan_id"
            )

    @property
    def current(self) -> PlanVersion:
        """Return the most recent immutable plan version."""

        return self.versions[-1]

    @property
    def mission_id(self) -> str:
        return self.current.mission.mission_id

    def get_version(self, version: int) -> PlanVersion:
        """Return one historical version."""

        if version < 1 or version > len(self.versions):
            raise IndexError(f"Plan version does not exist: {version}")

        return self.versions[version - 1]


def create_plan_version(
    *,
    mission: Mission,
    state: PlanState = PlanState.DRAFT,
    dependencies: tuple[Dependency, ...] = (),
    plan_id: str | None = None,
    version: int = 1,
    parent_version: int | None = None,
    revision_reason: str | None = None,
    created_by: str = "planning_director",
    notes: tuple[str, ...] = (),
) -> PlanVersion:
    """Convenience constructor for an immutable plan version."""

    return PlanVersion(
        plan_id=plan_id or new_identifier("plan"),
        version=version,
        parent_version=parent_version,
        mission=mission,
        state=state,
        dependencies=dependencies,
        revision_reason=revision_reason,
        created_by=created_by,
        notes=notes,
    )
