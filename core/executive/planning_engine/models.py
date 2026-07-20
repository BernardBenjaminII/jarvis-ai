"""Immutable contracts used by the deterministic planning engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from core.executive.planning_engine.enums import (
    BlockerType,
    ConfidenceBand,
    PlanningPolicy,
    ReadinessState,
    RecommendationType,
    TraceSeverity,
    WorkItemKind,
    WorkItemState,
)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return a shallow immutable mapping copy."""

    return MappingProxyType(dict(value or {}))


def _canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-safe structures."""

    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()

    if hasattr(value, "value"):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]

    if isinstance(value, set):
        return sorted(_canonicalize(item) for item in value)

    if hasattr(value, "to_dict"):
        return _canonicalize(value.to_dict())

    return value


def canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 fingerprint for a mapping."""

    encoded = json.dumps(
        _canonicalize(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class WorkItem:
    """Normalized node from the mission hierarchy."""

    item_id: str
    kind: WorkItemKind
    name: str
    parent_id: str | None = None
    priority: int = 50
    sequence: int = 0
    authorization_required: bool = False
    risk_score: float = 0.0
    estimated_effort: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("Work-item identifier cannot be empty")

        if not self.name.strip():
            raise ValueError("Work-item name cannot be empty")

        if not 0 <= self.priority <= 100:
            raise ValueError("Work-item priority must be between 0 and 100")

        if self.sequence < 0:
            raise ValueError("Work-item sequence cannot be negative")

        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("Risk score must be between 0.0 and 1.0")

        if self.estimated_effort <= 0.0:
            raise ValueError("Estimated effort must be greater than zero")

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind.value,
            "name": self.name,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "sequence": self.sequence,
            "authorization_required": self.authorization_required,
            "risk_score": self.risk_score,
            "estimated_effort": self.estimated_effort,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """Observed execution state for one work item."""

    item_id: str
    state: WorkItemState = WorkItemState.PENDING
    progress: float = 0.0
    authorization_granted: bool = False
    available_resources: tuple[str, ...] = ()
    satisfied_constraints: tuple[str, ...] = ()
    failure_reason: str | None = None
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("Execution-record identifier cannot be empty")

        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("Execution progress must be between 0.0 and 1.0")

        if (
            self.state is WorkItemState.COMPLETED
            and self.progress != 1.0
        ):
            object.__setattr__(self, "progress", 1.0)

        if (
            self.state is WorkItemState.FAILED
            and not self.failure_reason
        ):
            raise ValueError(
                "Failed execution records require a failure reason"
            )

        object.__setattr__(
            self,
            "available_resources",
            tuple(sorted(set(self.available_resources))),
        )
        object.__setattr__(
            self,
            "satisfied_constraints",
            tuple(sorted(set(self.satisfied_constraints))),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "state": self.state.value,
            "progress": self.progress,
            "authorization_granted": self.authorization_granted,
            "available_resources": list(self.available_resources),
            "satisfied_constraints": list(
                self.satisfied_constraints
            ),
            "failure_reason": self.failure_reason,
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    """Immutable point-in-time view of mission execution."""

    records: tuple[ExecutionRecord, ...] = ()
    captured_at: datetime = field(default_factory=utc_now)
    snapshot_id: str = ""

    def __post_init__(self) -> None:
        identifiers = [record.item_id for record in self.records]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Execution snapshot contains duplicate work-item records"
            )

        ordered = tuple(
            sorted(
                self.records,
                key=lambda record: record.item_id,
            )
        )
        object.__setattr__(self, "records", ordered)

        if not self.snapshot_id:
            payload = {
                "records": [
                    record.to_dict()
                    for record in ordered
                ],
                "captured_at": self.captured_at.isoformat(),
            }
            object.__setattr__(
                self,
                "snapshot_id",
                canonical_fingerprint(payload),
            )

    def get(self, item_id: str) -> ExecutionRecord:
        for record in self.records:
            if record.item_id == item_id:
                return record

        return ExecutionRecord(item_id=item_id)

    def contains(self, item_id: str) -> bool:
        return any(
            record.item_id == item_id
            for record in self.records
        )

    @classmethod
    def from_records(
        cls,
        records: Iterable[ExecutionRecord],
    ) -> "ExecutionSnapshot":
        return cls(records=tuple(records))

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at.isoformat(),
            "records": [
                record.to_dict()
                for record in self.records
            ],
        }


@dataclass(frozen=True, slots=True)
class Blocker:
    """Explainable condition preventing work from running."""

    item_id: str
    blocker_type: BlockerType
    reason: str
    blocking_item_ids: tuple[str, ...] = ()
    resolvable: bool = True

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Blocker reason cannot be empty")

        object.__setattr__(
            self,
            "blocking_item_ids",
            tuple(sorted(set(self.blocking_item_ids))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "blocker_type": self.blocker_type.value,
            "reason": self.reason,
            "blocking_item_ids": list(self.blocking_item_ids),
            "resolvable": self.resolvable,
        }


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    """Derived readiness and blocker details for a work item."""

    item_id: str
    state: ReadinessState
    blockers: tuple[Blocker, ...] = ()
    unmet_dependencies: tuple[str, ...] = ()
    score: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("Readiness score must be between 0 and 100")

        object.__setattr__(
            self,
            "blockers",
            tuple(
                sorted(
                    self.blockers,
                    key=lambda blocker: (
                        blocker.blocker_type.value,
                        blocker.reason,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "unmet_dependencies",
            tuple(sorted(set(self.unmet_dependencies))),
        )

    @property
    def runnable(self) -> bool:
        return self.state is ReadinessState.READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "state": self.state.value,
            "blockers": [
                blocker.to_dict()
                for blocker in self.blockers
            ],
            "unmet_dependencies": list(self.unmet_dependencies),
            "score": self.score,
            "runnable": self.runnable,
        }


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Auditable explanation emitted during analysis."""

    code: str
    message: str
    severity: TraceSeverity = TraceSeverity.INFO
    item_id: str | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Decision-trace code cannot be empty")

        if not self.message.strip():
            raise ValueError("Decision-trace message cannot be empty")

        object.__setattr__(
            self,
            "evidence",
            _freeze_mapping(self.evidence),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "item_id": self.item_id,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Deterministic next-action recommendation."""

    recommendation_type: RecommendationType
    item_id: str | None
    rationale: str
    score: float
    confidence: float
    confidence_band: ConfidenceBand
    alternatives: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("Recommendation rationale cannot be empty")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("Recommendation score must be between 0 and 100")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Recommendation confidence must be between 0.0 and 1.0"
            )

        object.__setattr__(
            self,
            "alternatives",
            tuple(self.alternatives),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_type": self.recommendation_type.value,
            "item_id": self.item_id,
            "rationale": self.rationale,
            "score": self.score,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band.value,
            "alternatives": list(self.alternatives),
        }


@dataclass(frozen=True, slots=True)
class PlanningAssessment:
    """Complete deterministic analysis of one plan version."""

    plan_id: str
    plan_version: int
    plan_fingerprint: str
    snapshot_id: str
    policy: PlanningPolicy
    readiness: tuple[ReadinessResult, ...]
    critical_path: tuple[str, ...]
    recommendation: Recommendation
    traces: tuple[DecisionTrace, ...]
    analyzed_at: datetime = field(default_factory=utc_now)
    assessment_id: str = ""

    def __post_init__(self) -> None:
        ordered_readiness = tuple(
            sorted(
                self.readiness,
                key=lambda result: result.item_id,
            )
        )
        object.__setattr__(
            self,
            "readiness",
            ordered_readiness,
        )

        if not self.assessment_id:
            payload = {
                "plan_id": self.plan_id,
                "plan_version": self.plan_version,
                "plan_fingerprint": self.plan_fingerprint,
                "snapshot_id": self.snapshot_id,
                "policy": self.policy.value,
                "readiness": [
                    result.to_dict()
                    for result in ordered_readiness
                ],
                "critical_path": list(self.critical_path),
                "recommendation": self.recommendation.to_dict(),
                "traces": [
                    trace.to_dict()
                    for trace in self.traces
                ],
            }
            object.__setattr__(
                self,
                "assessment_id",
                canonical_fingerprint(payload),
            )

    @property
    def runnable_item_ids(self) -> tuple[str, ...]:
        return tuple(
            result.item_id
            for result in self.readiness
            if result.state is ReadinessState.READY
        )

    @property
    def blocked_item_ids(self) -> tuple[str, ...]:
        return tuple(
            result.item_id
            for result in self.readiness
            if result.state is ReadinessState.BLOCKED
        )

    @property
    def complete(self) -> bool:
        terminal_states = {
            ReadinessState.COMPLETE,
            ReadinessState.TERMINAL,
        }

        return bool(self.readiness) and all(
            result.state in terminal_states
            for result in self.readiness
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "plan_id": self.plan_id,
            "plan_version": self.plan_version,
            "plan_fingerprint": self.plan_fingerprint,
            "snapshot_id": self.snapshot_id,
            "policy": self.policy.value,
            "analyzed_at": self.analyzed_at.isoformat(),
            "readiness": [
                result.to_dict()
                for result in self.readiness
            ],
            "runnable_item_ids": list(self.runnable_item_ids),
            "blocked_item_ids": list(self.blocked_item_ids),
            "critical_path": list(self.critical_path),
            "recommendation": self.recommendation.to_dict(),
            "traces": [
                trace.to_dict()
                for trace in self.traces
            ],
            "complete": self.complete,
        }
