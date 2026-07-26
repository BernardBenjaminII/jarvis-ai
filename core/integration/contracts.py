"""Canonical contracts for the JARVIS Executive Projection Plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .enums import (
    CapabilityLifecycle,
    HealthStatus,
    IntegrationStatus,
    KnowledgeCoverageStatus,
    Severity,
    VisibilitySurface,
)
from .errors import InvalidIntegrationDefinitionError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_text(value: object, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise InvalidIntegrationDefinitionError(f"{field_name} is required")
    return normalized


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidIntegrationDefinitionError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidIntegrationDefinitionError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((value or {}).items(), key=lambda item: item[0]))
    )


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return value


class ProjectionStatus(str, Enum):
    """Availability state of a provider projection."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"
    UNKNOWN = "unknown"


_STATUS_PRIORITY = {
    ProjectionStatus.UNAVAILABLE: 5,
    ProjectionStatus.DEGRADED: 4,
    ProjectionStatus.UNKNOWN: 3,
    ProjectionStatus.NOT_CONFIGURED: 2,
    ProjectionStatus.AVAILABLE: 1,
}


@dataclass(frozen=True, slots=True)
class ProjectionHealth:
    status: ProjectionStatus
    summary: str
    details: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    warnings: Tuple[str, ...] = ()
    errors: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, ProjectionStatus):
            try:
                object.__setattr__(
                    self,
                    "status",
                    ProjectionStatus(self.status),
                )
            except (TypeError, ValueError) as exc:
                raise InvalidIntegrationDefinitionError(
                    f"invalid projection status: {self.status!r}"
                ) from exc

        object.__setattr__(
            self,
            "summary",
            _require_text(self.summary, "summary"),
        )
        object.__setattr__(self, "details", _freeze_mapping(self.details))
        object.__setattr__(
            self,
            "warnings",
            tuple(str(item) for item in self.warnings),
        )
        object.__setattr__(
            self,
            "errors",
            tuple(str(item) for item in self.errors),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "summary": self.summary,
            "details": _serialize(self.details),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(frozen=True, slots=True)
class ProjectionEnvelope:
    projection_id: str
    schema_version: str
    generated_at: datetime
    source_timestamp: datetime | None
    provider: str
    health: ProjectionHealth
    data: Mapping[str, Any]
    warnings: Tuple[str, ...] = ()
    errors: Tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "projection_id",
            _require_text(self.projection_id, "projection_id"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "provider",
            _require_text(self.provider, "provider"),
        )
        object.__setattr__(
            self,
            "generated_at",
            _aware_utc(self.generated_at, "generated_at"),
        )

        if self.source_timestamp is not None:
            object.__setattr__(
                self,
                "source_timestamp",
                _aware_utc(self.source_timestamp, "source_timestamp"),
            )

        if not isinstance(self.health, ProjectionHealth):
            raise InvalidIntegrationDefinitionError(
                "health must be a ProjectionHealth"
            )

        object.__setattr__(self, "data", _freeze_mapping(self.data))
        object.__setattr__(
            self,
            "warnings",
            tuple(str(item) for item in self.warnings),
        )
        object.__setattr__(
            self,
            "errors",
            tuple(str(item) for item in self.errors),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

    @property
    def available(self) -> bool:
        return self.health.status in {
            ProjectionStatus.AVAILABLE,
            ProjectionStatus.DEGRADED,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "source_timestamp": (
                self.source_timestamp.isoformat()
                if self.source_timestamp is not None
                else None
            ),
            "provider": self.provider,
            "health": self.health.to_dict(),
            "data": _serialize(self.data),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": _serialize(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExecutiveProjection:
    generated_at: datetime
    projections: Tuple[ProjectionEnvelope, ...]
    overall_status: ProjectionStatus
    warnings: Tuple[str, ...] = ()
    errors: Tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _aware_utc(self.generated_at, "generated_at"),
        )
        object.__setattr__(self, "projections", tuple(self.projections))

        for projection in self.projections:
            if not isinstance(projection, ProjectionEnvelope):
                raise InvalidIntegrationDefinitionError(
                    "projections must contain ProjectionEnvelope values"
                )

        if not isinstance(self.overall_status, ProjectionStatus):
            object.__setattr__(
                self,
                "overall_status",
                ProjectionStatus(self.overall_status),
            )

        object.__setattr__(
            self,
            "warnings",
            tuple(str(item) for item in self.warnings),
        )
        object.__setattr__(
            self,
            "errors",
            tuple(str(item) for item in self.errors),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

    @classmethod
    def from_envelopes(
        cls,
        projections: Tuple[ProjectionEnvelope, ...],
    ) -> "ExecutiveProjection":
        ordered = tuple(
            sorted(projections, key=lambda item: item.projection_id)
        )

        if ordered:
            overall = max(
                (item.health.status for item in ordered),
                key=lambda status: _STATUS_PRIORITY[status],
            )
        else:
            overall = ProjectionStatus.NOT_CONFIGURED

        warnings = tuple(
            message
            for projection in ordered
            for message in (
                *projection.health.warnings,
                *projection.warnings,
            )
        )
        errors = tuple(
            message
            for projection in ordered
            for message in (
                *projection.health.errors,
                *projection.errors,
            )
        )

        return cls(
            generated_at=datetime.now(timezone.utc),
            projections=ordered,
            overall_status=overall,
            warnings=warnings,
            errors=errors,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_status": self.overall_status.value,
            "projections": [
                projection.to_dict()
                for projection in self.projections
            ],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": _serialize(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VerificationReference:
    verifier: str
    fingerprint: str = ""
    last_verified_at: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "verifier",
            _require_text(self.verifier, "verifier"),
        )


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str
    name: str
    description: str
    owner_package: str
    lifecycle: CapabilityLifecycle
    health: HealthStatus
    dependencies: Tuple[str, ...] = ()
    input_contracts: Tuple[str, ...] = ()
    output_contracts: Tuple[str, ...] = ()
    api_routes: Tuple[str, ...] = ()
    ui_surfaces: Tuple[str, ...] = ()
    knowledge_requirements: Tuple[str, ...] = ()
    executor_capabilities: Tuple[str, ...] = ()
    visibility: Tuple[VisibilitySurface, ...] = ()
    verification: VerificationReference | None = None
    metadata: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability_id",
            _require_text(self.capability_id, "capability_id"),
        )
        object.__setattr__(self, "name", _require_text(self.name, "name"))
        object.__setattr__(
            self,
            "owner_package",
            _require_text(self.owner_package, "owner_package"),
        )
        for name in (
            "dependencies",
            "input_contracts",
            "output_contracts",
            "api_routes",
            "ui_surfaces",
            "knowledge_requirements",
            "executor_capabilities",
            "visibility",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class IntegrationLink:
    source_capability: str
    target_capability: str
    status: IntegrationStatus
    transport: str
    contract: str
    observable: bool
    details: str = ""


@dataclass(frozen=True, slots=True)
class IntegrationFinding:
    finding_id: str
    severity: Severity
    capability_id: str
    surface: VisibilitySurface
    summary: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class KnowledgeReadiness:
    query: str
    status: KnowledgeCoverageStatus
    coverage: float
    known_domains: Tuple[str, ...] = ()
    missing_domains: Tuple[str, ...] = ()
    recommended_sources: Tuple[str, ...] = ()
    can_proceed: bool = False
    confidence_limit: float = 0.0
    catalog_reference: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.coverage <= 1:
            raise InvalidIntegrationDefinitionError(
                "coverage must be between 0 and 1"
            )
        if not 0 <= self.confidence_limit <= 1:
            raise InvalidIntegrationDefinitionError(
                "confidence_limit must be between 0 and 1"
            )
        for name in (
            "known_domains",
            "missing_domains",
            "recommended_sources",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class CapabilityProjection:
    capability_id: str
    name: str
    lifecycle: CapabilityLifecycle
    health: HealthStatus
    runtime_visible: bool
    api_visible: bool
    ui_visible: bool
    knowledge_connected: bool
    telemetry_visible: bool
    dependencies: Tuple[str, ...]
    api_routes: Tuple[str, ...]
    ui_surfaces: Tuple[str, ...]
    verification_fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "api_routes", tuple(self.api_routes))
        object.__setattr__(self, "ui_surfaces", tuple(self.ui_surfaces))


@dataclass(frozen=True, slots=True)
class IntegrationHealthProjection:
    generated_at: str
    overall_health: HealthStatus
    capabilities: Tuple[CapabilityProjection, ...]
    links: Tuple[IntegrationLink, ...]
    findings: Tuple[IntegrationFinding, ...]
    totals: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "links", tuple(self.links))
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "totals", _freeze_mapping(self.totals))


@dataclass(frozen=True, slots=True)
class CommanderBriefProjection:
    generated_at: str
    system_health: HealthStatus
    available_capabilities: int
    degraded_capabilities: int
    unavailable_capabilities: int
    not_connected_capabilities: int
    pending_approvals: int
    active_missions: int
    failed_activities: int
    acquisition_queue_depth: int
    critical_findings: Tuple[IntegrationFinding, ...]
    knowledge_readiness: KnowledgeReadiness | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "critical_findings",
            tuple(self.critical_findings),
        )


@dataclass(frozen=True, slots=True)
class ExecutiveTimelineNode:
    node_id: str
    node_type: str
    status: str
    title: str
    parent_id: str = ""
    timestamp: str = ""
    trace_reference: str = ""


@dataclass(frozen=True, slots=True)
class MissionControlProjection:
    commander_brief: CommanderBriefProjection
    capability_catalog: Tuple[CapabilityProjection, ...]
    integration_health: IntegrationHealthProjection
    executive_timeline: Tuple[ExecutiveTimelineNode, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability_catalog",
            tuple(self.capability_catalog),
        )
        object.__setattr__(
            self,
            "executive_timeline",
            tuple(self.executive_timeline),
        )


__all__ = [
    "CapabilityDefinition",
    "CapabilityProjection",
    "CommanderBriefProjection",
    "ExecutiveProjection",
    "ExecutiveTimelineNode",
    "IntegrationFinding",
    "IntegrationHealthProjection",
    "IntegrationLink",
    "KnowledgeReadiness",
    "MissionControlProjection",
    "ProjectionEnvelope",
    "ProjectionHealth",
    "ProjectionStatus",
    "VerificationReference",
    "utc_now_iso",
]
