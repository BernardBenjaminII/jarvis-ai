"""Immutable domain contracts for JARVIS Architecture Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .enums import (
    CertificationStatus,
    CompatibilityStatus,
    DependencyKind,
    FindingCategory,
    FindingSeverity,
    MigrationStatus,
    OwnershipStatus,
    SymbolKind,
)
from .errors import ArchitectureValidationError
from .fingerprints import architecture_fingerprint, canonical_json


def _require_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ArchitectureValidationError(f"{field_name} must not be empty")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not value:
        return MappingProxyType({})
    return MappingProxyType(dict(sorted(value.items(), key=lambda item: item[0])))


@dataclass(frozen=True, slots=True)
class SerializableArchitectureContract:
    """Base behavior for immutable architecture contracts."""

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


@dataclass(frozen=True, slots=True)
class PublicSymbol(SerializableArchitectureContract):
    name: str
    qualified_name: str
    kind: SymbolKind
    module: str
    signature: str | None = None
    exported: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_text(self.name, "name"))
        object.__setattr__(
            self, "qualified_name", _require_text(self.qualified_name, "qualified_name")
        )
        object.__setattr__(self, "module", _require_text(self.module, "module"))
        object.__setattr__(self, "signature", _normalize_optional_text(self.signature))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class ModuleDefinition(SerializableArchitectureContract):
    path: str
    module: str
    line_count: int
    symbols: tuple[PublicSymbol, ...] = ()
    imports: tuple[str, ...] = ()
    public_exports: tuple[str, ...] = ()
    content_fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _require_text(self.path, "path"))
        object.__setattr__(self, "module", _require_text(self.module, "module"))
        if self.line_count < 0:
            raise ArchitectureValidationError("line_count must be non-negative")
        object.__setattr__(self, "symbols", tuple(self.symbols))
        object.__setattr__(self, "imports", tuple(sorted(set(self.imports))))
        object.__setattr__(
            self, "public_exports", tuple(sorted(set(self.public_exports)))
        )
        object.__setattr__(
            self,
            "content_fingerprint",
            _normalize_optional_text(self.content_fingerprint),
        )


@dataclass(frozen=True, slots=True)
class SubsystemDefinition(SerializableArchitectureContract):
    subsystem_id: str
    name: str
    canonical_package: str
    owned_concepts: tuple[str, ...] = ()
    allowed_dependencies: tuple[str, ...] = ()
    forbidden_dependencies: tuple[str, ...] = ()
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystem_id", _require_text(self.subsystem_id, "subsystem_id")
        )
        object.__setattr__(self, "name", _require_text(self.name, "name"))
        object.__setattr__(
            self,
            "canonical_package",
            _require_text(self.canonical_package, "canonical_package"),
        )
        object.__setattr__(
            self, "owned_concepts", tuple(sorted(set(self.owned_concepts)))
        )
        object.__setattr__(
            self,
            "allowed_dependencies",
            tuple(sorted(set(self.allowed_dependencies))),
        )
        object.__setattr__(
            self,
            "forbidden_dependencies",
            tuple(sorted(set(self.forbidden_dependencies))),
        )
        object.__setattr__(
            self, "description", _normalize_optional_text(self.description)
        )

        overlap = set(self.allowed_dependencies) & set(self.forbidden_dependencies)
        if overlap:
            raise ArchitectureValidationError(
                f"Dependencies cannot be both allowed and forbidden: {sorted(overlap)}"
            )


@dataclass(frozen=True, slots=True)
class OwnershipDeclaration(SerializableArchitectureContract):
    concept: str
    canonical_owner: str
    status: OwnershipStatus = OwnershipStatus.CANONICAL
    legacy_owners: tuple[str, ...] = ()
    rationale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept", _require_text(self.concept, "concept"))
        object.__setattr__(
            self,
            "canonical_owner",
            _require_text(self.canonical_owner, "canonical_owner"),
        )
        object.__setattr__(
            self, "legacy_owners", tuple(sorted(set(self.legacy_owners)))
        )
        object.__setattr__(self, "rationale", _normalize_optional_text(self.rationale))

        if self.canonical_owner in self.legacy_owners:
            raise ArchitectureValidationError(
                "canonical_owner cannot also appear in legacy_owners"
            )


@dataclass(frozen=True, slots=True)
class DependencyEdge(SerializableArchitectureContract):
    source: str
    target: str
    kind: DependencyKind = DependencyKind.IMPORT
    evidence: tuple[str, ...] = ()
    permitted: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _require_text(self.source, "source"))
        object.__setattr__(self, "target", _require_text(self.target, "target"))
        object.__setattr__(self, "evidence", tuple(sorted(set(self.evidence))))
        if self.source == self.target:
            raise ArchitectureValidationError(
                "DependencyEdge source and target must differ"
            )


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment(SerializableArchitectureContract):
    subject: str
    candidate: str
    status: CompatibilityStatus
    matched_symbols: tuple[str, ...] = ()
    missing_symbols: tuple[str, ...] = ()
    unique_symbols: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", _require_text(self.subject, "subject"))
        object.__setattr__(self, "candidate", _require_text(self.candidate, "candidate"))
        object.__setattr__(
            self, "matched_symbols", tuple(sorted(set(self.matched_symbols)))
        )
        object.__setattr__(
            self, "missing_symbols", tuple(sorted(set(self.missing_symbols)))
        )
        object.__setattr__(
            self, "unique_symbols", tuple(sorted(set(self.unique_symbols)))
        )
        object.__setattr__(self, "notes", tuple(self.notes))


@dataclass(frozen=True, slots=True)
class ArchitectureFinding(SerializableArchitectureContract):
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    affected_paths: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    remediation: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "finding_id", _require_text(self.finding_id, "finding_id")
        )
        object.__setattr__(self, "title", _require_text(self.title, "title"))
        object.__setattr__(
            self, "description", _require_text(self.description, "description")
        )
        object.__setattr__(
            self, "affected_paths", tuple(sorted(set(self.affected_paths)))
        )
        object.__setattr__(self, "evidence", tuple(sorted(set(self.evidence))))
        object.__setattr__(
            self, "remediation", _normalize_optional_text(self.remediation)
        )


@dataclass(frozen=True, slots=True)
class MigrationStep(SerializableArchitectureContract):
    order: int
    step_id: str
    description: str
    status: MigrationStatus = MigrationStatus.PLANNED
    prerequisites: tuple[str, ...] = ()
    verification: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ArchitectureValidationError("order must be at least 1")
        object.__setattr__(self, "step_id", _require_text(self.step_id, "step_id"))
        object.__setattr__(
            self, "description", _require_text(self.description, "description")
        )
        object.__setattr__(
            self, "prerequisites", tuple(sorted(set(self.prerequisites)))
        )
        object.__setattr__(self, "verification", tuple(self.verification))


@dataclass(frozen=True, slots=True)
class MigrationPlan(SerializableArchitectureContract):
    plan_id: str
    subject: str
    target_owner: str
    status: MigrationStatus
    steps: tuple[MigrationStep, ...]
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _require_text(self.plan_id, "plan_id"))
        object.__setattr__(self, "subject", _require_text(self.subject, "subject"))
        object.__setattr__(
            self, "target_owner", _require_text(self.target_owner, "target_owner")
        )
        ordered_steps = tuple(sorted(self.steps, key=lambda step: step.order))
        orders = [step.order for step in ordered_steps]
        if len(set(orders)) != len(orders):
            raise ArchitectureValidationError("Migration step order values must be unique")
        object.__setattr__(self, "steps", ordered_steps)
        object.__setattr__(self, "blockers", tuple(sorted(set(self.blockers))))


@dataclass(frozen=True, slots=True)
class CertificationRecord(SerializableArchitectureContract):
    release_id: str
    status: CertificationStatus
    checks_passed: int
    checks_failed: int
    guarantees: tuple[str, ...] = ()
    compatibility_promises: tuple[str, ...] = ()
    architecture_fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "release_id", _require_text(self.release_id, "release_id")
        )
        if self.checks_passed < 0 or self.checks_failed < 0:
            raise ArchitectureValidationError(
                "Certification check counts must be non-negative"
            )
        if self.status is CertificationStatus.PASSED and self.checks_failed:
            raise ArchitectureValidationError(
                "Passed certification cannot contain failed checks"
            )
        object.__setattr__(
            self, "guarantees", tuple(sorted(set(self.guarantees)))
        )
        object.__setattr__(
            self,
            "compatibility_promises",
            tuple(sorted(set(self.compatibility_promises))),
        )
        object.__setattr__(
            self,
            "architecture_fingerprint",
            _normalize_optional_text(self.architecture_fingerprint),
        )


@dataclass(frozen=True, slots=True)
class ArchitectureSnapshot(SerializableArchitectureContract):
    snapshot_id: str
    repository_root: str
    branch: str
    commit: str
    modules: tuple[ModuleDefinition, ...] = ()
    subsystems: tuple[SubsystemDefinition, ...] = ()
    ownership: tuple[OwnershipDeclaration, ...] = ()
    dependencies: tuple[DependencyEdge, ...] = ()
    findings: tuple[ArchitectureFinding, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "snapshot_id", _require_text(self.snapshot_id, "snapshot_id")
        )
        object.__setattr__(
            self,
            "repository_root",
            _require_text(self.repository_root, "repository_root"),
        )
        object.__setattr__(self, "branch", _require_text(self.branch, "branch"))
        object.__setattr__(self, "commit", _require_text(self.commit, "commit"))
        object.__setattr__(
            self, "modules", tuple(sorted(self.modules, key=lambda item: item.path))
        )
        object.__setattr__(
            self,
            "subsystems",
            tuple(sorted(self.subsystems, key=lambda item: item.subsystem_id)),
        )
        object.__setattr__(
            self,
            "ownership",
            tuple(sorted(self.ownership, key=lambda item: item.concept)),
        )
        object.__setattr__(
            self,
            "dependencies",
            tuple(sorted(self.dependencies, key=lambda item: (item.source, item.target))),
        )
        object.__setattr__(
            self,
            "findings",
            tuple(sorted(self.findings, key=lambda item: item.finding_id)),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = [
    "ArchitectureFinding",
    "ArchitectureSnapshot",
    "CertificationRecord",
    "CompatibilityAssessment",
    "DependencyEdge",
    "MigrationPlan",
    "MigrationStep",
    "ModuleDefinition",
    "OwnershipDeclaration",
    "PublicSymbol",
    "SerializableArchitectureContract",
    "SubsystemDefinition",
]
