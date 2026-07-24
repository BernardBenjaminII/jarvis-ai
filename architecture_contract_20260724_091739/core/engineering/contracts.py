from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.architecture import architecture_fingerprint, canonical_json
from .enums import (
    ChangeKind, ChangeRisk, DecisionStatus, EvidenceStatus,
    GateStatus, VerificationKind,
)
from .errors import EngineeringValidationError

def _text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise EngineeringValidationError(f"{name} must not be empty")
    return value

def _items(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))

def _mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((value or {}).items())))

@dataclass(frozen=True, slots=True)
class EngineeringContract:
    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)

@dataclass(frozen=True, slots=True)
class EngineeringPrinciple(EngineeringContract):
    principle_id: str
    title: str
    statement: str
    rationale: str
    mandatory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "principle_id", _text(self.principle_id, "principle_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "statement", _text(self.statement, "statement"))
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))

@dataclass(frozen=True, slots=True)
class ChangeProposal(EngineeringContract):
    change_id: str
    title: str
    kind: ChangeKind
    risk: ChangeRisk
    purpose: str
    affected_subsystems: tuple[str, ...]
    owners: tuple[str, ...]
    affected_public_apis: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    rollback_strategy: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "purpose", _text(self.purpose, "purpose"))
        object.__setattr__(self, "affected_subsystems", _items(self.affected_subsystems))
        object.__setattr__(self, "owners", _items(self.owners))
        object.__setattr__(self, "affected_public_apis", _items(self.affected_public_apis))
        object.__setattr__(self, "verification_requirements", _items(self.verification_requirements))
        object.__setattr__(self, "metadata", _mapping(self.metadata))
        if not self.affected_subsystems:
            raise EngineeringValidationError("affected_subsystems must not be empty")
        if not self.owners:
            raise EngineeringValidationError("owners must not be empty")
        if self.risk in {ChangeRisk.HIGH, ChangeRisk.CRITICAL} and not self.rollback_strategy:
            raise EngineeringValidationError("high-risk changes require rollback_strategy")

@dataclass(frozen=True, slots=True)
class VerificationEvidence(EngineeringContract):
    evidence_id: str
    change_id: str
    kind: VerificationKind
    status: EvidenceStatus
    verifier: str
    command: str
    checks_passed: int
    checks_failed: int
    artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "verifier", _text(self.verifier, "verifier"))
        object.__setattr__(self, "command", _text(self.command, "command"))
        object.__setattr__(self, "artifacts", _items(self.artifacts))
        if self.checks_passed < 0 or self.checks_failed < 0:
            raise EngineeringValidationError("check counts must be non-negative")
        if self.status is EvidenceStatus.SUFFICIENT and self.checks_failed:
            raise EngineeringValidationError("sufficient evidence cannot contain failures")

@dataclass(frozen=True, slots=True)
class EngineeringGate(EngineeringContract):
    gate_id: str
    name: str
    status: GateStatus
    required_evidence_kinds: tuple[VerificationKind, ...]
    evidence_ids: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _text(self.gate_id, "gate_id"))
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "required_evidence_kinds", tuple(sorted(set(self.required_evidence_kinds), key=lambda x: x.value)))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids))
        object.__setattr__(self, "blockers", _items(self.blockers))
        if self.status is GateStatus.PASSED and self.blockers:
            raise EngineeringValidationError("passed gate cannot contain blockers")
        if self.status is GateStatus.FAILED and not self.blockers:
            raise EngineeringValidationError("failed gate must identify blockers")

@dataclass(frozen=True, slots=True)
class GovernanceDecision(EngineeringContract):
    decision_id: str
    change_id: str
    status: DecisionStatus
    authority: str
    rationale: str
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids))
        if self.status is DecisionStatus.APPROVED and not self.evidence_ids:
            raise EngineeringValidationError("approved decision requires evidence")

@dataclass(frozen=True, slots=True)
class EngineeringAssessment(EngineeringContract):
    assessment_id: str
    proposal: ChangeProposal
    evidence: tuple[VerificationEvidence, ...]
    gates: tuple[EngineeringGate, ...]
    decision: GovernanceDecision | None = None
    explainability_improvements: tuple[str, ...] = ()
    remaining_uncertainties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", _text(self.assessment_id, "assessment_id"))
        object.__setattr__(self, "evidence", tuple(sorted(self.evidence, key=lambda x: x.evidence_id)))
        object.__setattr__(self, "gates", tuple(sorted(self.gates, key=lambda x: x.gate_id)))
        object.__setattr__(self, "explainability_improvements", _items(self.explainability_improvements))
        object.__setattr__(self, "remaining_uncertainties", _items(self.remaining_uncertainties))
        known = {item.evidence_id for item in self.evidence}
        if self.decision:
            missing = set(self.decision.evidence_ids) - known
            if missing:
                raise EngineeringValidationError(f"unknown evidence IDs: {sorted(missing)}")

__all__ = [
    "ChangeProposal", "EngineeringAssessment", "EngineeringContract",
    "EngineeringGate", "EngineeringPrinciple", "GovernanceDecision",
    "VerificationEvidence",
]
