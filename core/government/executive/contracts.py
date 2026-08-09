"""Immutable Executive integration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping

from core.government.models import (
    ConstitutionalIdentifier,
    HealthState,
    ReadinessState,
)
from core.government.registry import GovernmentSnapshot
from core.government.relationships import OrganizationalGraph

from .enums import (
    AssessmentState,
    AssignmentState,
    DirectiveState,
    RecommendationPriority,
    RecommendationState,
)


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class DepartmentAssessment:
    department: ConstitutionalIdentifier
    state: AssessmentState
    health: HealthState
    readiness: ReadinessState
    summary: str
    risks: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("assessment summary is required")
        object.__setattr__(self, "summary", self.summary.strip())
        object.__setattr__(
            self,
            "risks",
            tuple(sorted({item.strip() for item in self.risks if item.strip()})),
        )
        object.__setattr__(
            self,
            "recommendations",
            tuple(
                sorted(
                    {item.strip() for item in self.recommendations if item.strip()}
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class OrganizationalAssessment:
    state: AssessmentState
    summary: str
    departments: tuple[DepartmentAssessment, ...] = ()
    significant_risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("organizational assessment summary is required")
        object.__setattr__(self, "summary", self.summary.strip())
        object.__setattr__(
            self,
            "departments",
            tuple(
                sorted(
                    self.departments,
                    key=lambda item: item.department.value,
                )
            ),
        )
        object.__setattr__(
            self,
            "significant_risks",
            tuple(
                sorted(
                    {
                        item.strip()
                        for item in self.significant_risks
                        if item.strip()
                    }
                )
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "state": self.state.value,
                "summary": self.summary,
                "departments": [
                    {
                        "department": item.department.value,
                        "state": item.state.value,
                        "health": item.health.value,
                        "readiness": item.readiness.value,
                        "summary": item.summary,
                        "risks": list(item.risks),
                        "recommendations": list(item.recommendations),
                    }
                    for item in self.departments
                ],
                "significant_risks": list(self.significant_risks),
            }
        )


@dataclass(frozen=True, slots=True)
class ExecutiveRecommendation:
    recommendation_id: str
    title: str
    rationale: str
    priority: RecommendationPriority
    responsible_organization: ConstitutionalIdentifier
    supporting_evidence: tuple[str, ...] = ()
    state: RecommendationState = RecommendationState.PROPOSED

    def __post_init__(self) -> None:
        if not self.recommendation_id.strip():
            raise ValueError("recommendation_id is required")
        if not self.title.strip():
            raise ValueError("recommendation title is required")
        if not self.rationale.strip():
            raise ValueError("recommendation rationale is required")
        object.__setattr__(self, "recommendation_id", self.recommendation_id.strip())
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "rationale", self.rationale.strip())
        object.__setattr__(
            self,
            "supporting_evidence",
            tuple(
                sorted(
                    {
                        item.strip()
                        for item in self.supporting_evidence
                        if item.strip()
                    }
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class DirectiveRequest:
    directive_id: str
    issuing_authority: ConstitutionalIdentifier
    responsible_organization: ConstitutionalIdentifier
    purpose: str
    required_action: str
    expected_outcome: str
    constitutional_basis: tuple[str, ...]
    state: DirectiveState = DirectiveState.DRAFT

    def __post_init__(self) -> None:
        for name in (
            "directive_id",
            "purpose",
            "required_action",
            "expected_outcome",
        ):
            value = getattr(self, name).strip()
            if not value:
                raise ValueError(f"{name} is required")
            object.__setattr__(self, name, value)
        if self.issuing_authority == self.responsible_organization:
            raise ValueError(
                "issuing authority and responsible organization must differ"
            )
        basis = tuple(
            sorted(
                {
                    item.strip()
                    for item in self.constitutional_basis
                    if item.strip()
                }
            )
        )
        if not basis:
            raise ValueError("constitutional_basis is required")
        object.__setattr__(self, "constitutional_basis", basis)


@dataclass(frozen=True, slots=True)
class AssignmentRequest:
    assignment_id: str
    subject: ConstitutionalIdentifier
    assignee: ConstitutionalIdentifier
    objective: str
    state: AssignmentState = AssignmentState.PROPOSED
    dependencies: tuple[ConstitutionalIdentifier, ...] = ()

    def __post_init__(self) -> None:
        if not self.assignment_id.strip():
            raise ValueError("assignment_id is required")
        if not self.objective.strip():
            raise ValueError("assignment objective is required")
        if self.subject == self.assignee:
            raise ValueError("assignment subject cannot assign itself")
        object.__setattr__(self, "assignment_id", self.assignment_id.strip())
        object.__setattr__(self, "objective", self.objective.strip())
        object.__setattr__(
            self,
            "dependencies",
            tuple(
                sorted(
                    set(self.dependencies),
                    key=lambda item: item.value,
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class DepartmentReport:
    department: ConstitutionalIdentifier
    health: HealthState
    readiness: ReadinessState
    summary: str
    metrics: Mapping[str, str] = field(default_factory=dict)
    risks: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("department report summary is required")
        object.__setattr__(self, "summary", self.summary.strip())
        object.__setattr__(
            self,
            "metrics",
            dict(
                sorted(
                    (str(key), str(value))
                    for key, value in self.metrics.items()
                )
            ),
        )
        object.__setattr__(
            self,
            "risks",
            tuple(sorted({item.strip() for item in self.risks if item.strip()})),
        )
        object.__setattr__(
            self,
            "recommendations",
            tuple(
                sorted(
                    {item.strip() for item in self.recommendations if item.strip()}
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class ExecutiveGovernmentView:
    government: GovernmentSnapshot
    graph: OrganizationalGraph
    assessment: OrganizationalAssessment
    reports: tuple[DepartmentReport, ...] = ()
    recommendations: tuple[ExecutiveRecommendation, ...] = ()

    def __post_init__(self) -> None:
        if self.government.graph != self.graph:
            raise ValueError(
                "Executive Government view graph does not match snapshot"
            )
        object.__setattr__(
            self,
            "reports",
            tuple(
                sorted(
                    self.reports,
                    key=lambda item: item.department.value,
                )
            ),
        )
        object.__setattr__(
            self,
            "recommendations",
            tuple(
                sorted(
                    self.recommendations,
                    key=lambda item: (
                        item.priority.value,
                        item.recommendation_id,
                    ),
                )
            ),
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "government": self.government.fingerprint,
                "graph": self.graph.fingerprint,
                "assessment": self.assessment.fingerprint,
                "reports": [
                    {
                        "department": report.department.value,
                        "health": report.health.value,
                        "readiness": report.readiness.value,
                        "summary": report.summary,
                        "metrics": dict(report.metrics),
                        "risks": list(report.risks),
                        "recommendations": list(report.recommendations),
                    }
                    for report in self.reports
                ],
                "recommendations": [
                    {
                        "recommendation_id": item.recommendation_id,
                        "title": item.title,
                        "rationale": item.rationale,
                        "priority": item.priority.value,
                        "responsible_organization":
                            item.responsible_organization.value,
                        "supporting_evidence":
                            list(item.supporting_evidence),
                        "state": item.state.value,
                    }
                    for item in self.recommendations
                ],
            }
        )


@dataclass(frozen=True, slots=True)
class ExecutiveGovernmentSnapshot:
    snapshot_id: str
    view: ExecutiveGovernmentView

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        object.__setattr__(self, "snapshot_id", self.snapshot_id.strip())

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "snapshot_id": self.snapshot_id,
                "view": self.view.fingerprint,
            }
        )
