#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

mkdir -p \
    core/architecture \
    docs/architecture \
    tests \
    dev/verification

cat > core/architecture/enums.py <<'PYEOF'
"""Stable enumerations for JARVIS Architecture Intelligence."""

from __future__ import annotations

from enum import Enum


class StableStringEnum(str, Enum):
    """String-backed enum with stable serialization behavior."""

    def __str__(self) -> str:
        return self.value


class FindingSeverity(StableStringEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FindingCategory(StableStringEnum):
    OWNERSHIP = "ownership"
    DEPENDENCY = "dependency"
    COMPATIBILITY = "compatibility"
    DUPLICATION = "duplication"
    SYNTAX = "syntax"
    RELEASE = "release"
    MIGRATION = "migration"
    DRIFT = "drift"
    DOCUMENTATION = "documentation"


class OwnershipStatus(StableStringEnum):
    CANONICAL = "canonical"
    LEGACY = "legacy"
    AMBIGUOUS = "ambiguous"
    UNOWNED = "unowned"
    COMPATIBILITY_ALIAS = "compatibility_alias"


class CompatibilityStatus(StableStringEnum):
    EQUIVALENT = "equivalent"
    COMPATIBLE = "compatible"
    ADAPTER_REQUIRED = "adapter_required"
    MIGRATION_REQUIRED = "migration_required"
    UNIQUE = "unique"
    INCOMPARABLE = "incomparable"
    UNKNOWN = "unknown"


class MigrationStatus(StableStringEnum):
    NOT_REQUIRED = "not_required"
    PLANNED = "planned"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    COMPLETE = "complete"


class CertificationStatus(StableStringEnum):
    UNASSESSED = "unassessed"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SymbolKind(StableStringEnum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ENUM = "enum"
    CONSTANT = "constant"
    EXPORT = "export"


class DependencyKind(StableStringEnum):
    IMPORT = "import"
    RUNTIME = "runtime"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"


__all__ = [
    "CertificationStatus",
    "CompatibilityStatus",
    "DependencyKind",
    "FindingCategory",
    "FindingSeverity",
    "MigrationStatus",
    "OwnershipStatus",
    "StableStringEnum",
    "SymbolKind",
]
PYEOF

cat > core/architecture/errors.py <<'PYEOF'
"""Architecture Intelligence exception hierarchy."""

from __future__ import annotations


class ArchitectureError(Exception):
    """Base error for Architecture Intelligence."""


class ArchitectureValidationError(ArchitectureError):
    """Raised when an architecture contract violates an invariant."""


class ArchitectureSerializationError(ArchitectureError):
    """Raised when architecture data cannot be serialized canonically."""


class ArchitectureFingerprintError(ArchitectureError):
    """Raised when a deterministic fingerprint cannot be produced."""


class ArchitectureOwnershipError(ArchitectureError):
    """Raised for invalid or conflicting ownership declarations."""


class ArchitectureDependencyError(ArchitectureError):
    """Raised for invalid dependency declarations or policies."""


class ArchitectureCompatibilityError(ArchitectureError):
    """Raised when compatibility analysis cannot be completed safely."""


class ArchitectureMigrationError(ArchitectureError):
    """Raised for invalid migration plans or transitions."""


class ArchitectureCertificationError(ArchitectureError):
    """Raised when certification requirements are invalid or incomplete."""


__all__ = [
    "ArchitectureCertificationError",
    "ArchitectureCompatibilityError",
    "ArchitectureDependencyError",
    "ArchitectureError",
    "ArchitectureFingerprintError",
    "ArchitectureMigrationError",
    "ArchitectureOwnershipError",
    "ArchitectureSerializationError",
    "ArchitectureValidationError",
]
PYEOF

cat > core/architecture/fingerprints.py <<'PYEOF'
"""Deterministic canonical serialization and fingerprint helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Any

from .errors import ArchitectureFingerprintError, ArchitectureSerializationError


def canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-compatible structures."""

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonicalize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, Path):
        return value.as_posix()

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: str(item)):
            normalized[str(key)] = canonicalize(value[key])
        return normalized

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, set | frozenset):
        normalized_items = [canonicalize(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonicalize(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise ArchitectureSerializationError(
        f"Unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Return deterministic compact JSON."""

    try:
        return json.dumps(
            canonicalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ArchitectureSerializationError(str(exc)) from exc


def architecture_fingerprint(value: Any, *, algorithm: str = "sha256") -> str:
    """Return a deterministic hexadecimal fingerprint."""

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ArchitectureFingerprintError(
            f"Unsupported fingerprint algorithm: {algorithm}"
        ) from exc

    digest.update(canonical_json(value).encode("utf-8"))
    return digest.hexdigest()


def file_fingerprint(path: str | Path, *, algorithm: str = "sha256") -> str:
    """Fingerprint a file's raw bytes."""

    file_path = Path(path)
    if not file_path.is_file():
        raise ArchitectureFingerprintError(f"File not found: {file_path}")

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ArchitectureFingerprintError(
            f"Unsupported fingerprint algorithm: {algorithm}"
        ) from exc

    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


__all__ = [
    "architecture_fingerprint",
    "canonical_json",
    "canonicalize",
    "file_fingerprint",
]
PYEOF

cat > core/architecture/contracts.py <<'PYEOF'
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
PYEOF

cat > core/architecture/__init__.py <<'PYEOF'
"""Public API for JARVIS Architecture Intelligence."""

from .contracts import (
    ArchitectureFinding,
    ArchitectureSnapshot,
    CertificationRecord,
    CompatibilityAssessment,
    DependencyEdge,
    MigrationPlan,
    MigrationStep,
    ModuleDefinition,
    OwnershipDeclaration,
    PublicSymbol,
    SerializableArchitectureContract,
    SubsystemDefinition,
)
from .enums import (
    CertificationStatus,
    CompatibilityStatus,
    DependencyKind,
    FindingCategory,
    FindingSeverity,
    MigrationStatus,
    OwnershipStatus,
    StableStringEnum,
    SymbolKind,
)
from .errors import (
    ArchitectureCertificationError,
    ArchitectureCompatibilityError,
    ArchitectureDependencyError,
    ArchitectureError,
    ArchitectureFingerprintError,
    ArchitectureMigrationError,
    ArchitectureOwnershipError,
    ArchitectureSerializationError,
    ArchitectureValidationError,
)
from .fingerprints import (
    architecture_fingerprint,
    canonical_json,
    canonicalize,
    file_fingerprint,
)

__all__ = [
    "ArchitectureCertificationError",
    "ArchitectureCompatibilityError",
    "ArchitectureDependencyError",
    "ArchitectureError",
    "ArchitectureFinding",
    "ArchitectureFingerprintError",
    "ArchitectureMigrationError",
    "ArchitectureOwnershipError",
    "ArchitectureSerializationError",
    "ArchitectureSnapshot",
    "ArchitectureValidationError",
    "CertificationRecord",
    "CertificationStatus",
    "CompatibilityAssessment",
    "CompatibilityStatus",
    "DependencyEdge",
    "DependencyKind",
    "FindingCategory",
    "FindingSeverity",
    "MigrationPlan",
    "MigrationStatus",
    "MigrationStep",
    "ModuleDefinition",
    "OwnershipDeclaration",
    "OwnershipStatus",
    "PublicSymbol",
    "SerializableArchitectureContract",
    "StableStringEnum",
    "SubsystemDefinition",
    "SymbolKind",
    "architecture_fingerprint",
    "canonical_json",
    "canonicalize",
    "file_fingerprint",
]
PYEOF

cat > docs/architecture/architecture_intelligence.md <<'EOF'
# JARVIS Architecture Intelligence

**Status:** Genesis V-A1 foundation  
**Canonical package:** `core.architecture`

## 1. Mission

Architecture Intelligence provides deterministic, machine-readable models for
describing, analyzing, governing, and certifying the JARVIS repository.

It exists to answer questions such as:

- What subsystems exist?
- Which subsystem owns a concept?
- What depends on what?
- Which public symbols are duplicated?
- Are two implementations compatible?
- What blocks a migration?
- Has a certified architecture drifted?
- Is a release ready for certification?

## 2. Separation of Responsibilities

`core.architecture` contains stable domain contracts and deterministic
primitives.

Repository scanning, Git inspection, report generation, and release tooling
remain under `dev/architecture` or `dev/verification`.

Production subsystems must not depend on development tooling.

## 3. Foundation Contracts

Genesis V-A1 introduces:

- `ArchitectureSnapshot`
- `SubsystemDefinition`
- `ModuleDefinition`
- `PublicSymbol`
- `DependencyEdge`
- `OwnershipDeclaration`
- `ArchitectureFinding`
- `CompatibilityAssessment`
- `MigrationPlan`
- `MigrationStep`
- `CertificationRecord`

These contracts are immutable and canonically serializable.

## 4. Deterministic Fingerprints

Every architecture contract can produce:

- canonical compact JSON;
- deterministic SHA-256 fingerprints.

Dictionary ordering, set ordering, enum serialization, dataclass field
serialization, tuples, lists, and paths are normalized deterministically.

## 5. Safety Boundary

Genesis V-A1 does not:

- scan the repository;
- modify source files;
- write Git state;
- delete packages;
- redirect imports;
- perform runtime orchestration;
- autonomously approve migrations.

It defines the vocabulary used by later Architecture Intelligence packs.

## 6. Planned Packs

- **V-A2:** Repository inventory engine.
- **V-A3:** Ownership registry and policy manifest.
- **V-B1:** Dependency governance.
- **V-B2:** Semantic equivalence analysis.
- **V-B3:** Migration planning.
- **V-C1:** Certification manifests.
- **V-C2:** Release readiness.
- **V-C3:** Architecture drift detection.

## 7. Governing Principle

Architecture Intelligence may observe, analyze, explain, and recommend.

Human authority approves source changes, migrations, deletions, and releases.
EOF

cat > tests/test_genesis_5a1_architecture_foundation.py <<'PYEOF'
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.architecture import (
    ArchitectureFinding,
    ArchitectureSnapshot,
    ArchitectureValidationError,
    CertificationRecord,
    CertificationStatus,
    DependencyEdge,
    FindingCategory,
    FindingSeverity,
    MigrationPlan,
    MigrationStatus,
    MigrationStep,
    ModuleDefinition,
    OwnershipDeclaration,
    OwnershipStatus,
    PublicSymbol,
    SubsystemDefinition,
    SymbolKind,
    architecture_fingerprint,
    canonical_json,
    canonicalize,
    file_fingerprint,
)


class ArchitectureFoundationTests(unittest.TestCase):
    def test_public_symbol_is_immutable(self) -> None:
        symbol = PublicSymbol(
            name="EvidenceRecord",
            qualified_name="core.evidence.EvidenceRecord",
            kind=SymbolKind.CLASS,
            module="core.evidence",
        )
        with self.assertRaises((AttributeError, TypeError)):
            symbol.name = "Changed"  # type: ignore[misc]

    def test_metadata_is_immutable(self) -> None:
        symbol = PublicSymbol(
            name="EvidenceRecord",
            qualified_name="core.evidence.EvidenceRecord",
            kind=SymbolKind.CLASS,
            module="core.evidence",
            metadata={"owner": "evidence"},
        )
        with self.assertRaises(TypeError):
            symbol.metadata["owner"] = "reasoning"  # type: ignore[index]

    def test_canonical_json_is_deterministic(self) -> None:
        left = {"b": 2, "a": {"z", "x", "y"}}
        right = {"a": {"y", "z", "x"}, "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))

    def test_fingerprint_is_deterministic(self) -> None:
        first = architecture_fingerprint({"b": 2, "a": 1})
        second = architecture_fingerprint({"a": 1, "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_contract_fingerprint_is_stable(self) -> None:
        module = ModuleDefinition(
            path="core/evidence/contracts.py",
            module="core.evidence.contracts",
            line_count=100,
            imports=("typing", "dataclasses", "typing"),
            public_exports=("EvidenceRecord", "Proposition"),
        )
        self.assertEqual(module.fingerprint(), module.fingerprint())

    def test_subsystem_dependency_overlap_is_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            SubsystemDefinition(
                subsystem_id="evidence",
                name="Evidence",
                canonical_package="core.evidence",
                allowed_dependencies=("core.reasoning",),
                forbidden_dependencies=("core.reasoning",),
            )

    def test_ownership_cannot_name_owner_as_legacy(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            OwnershipDeclaration(
                concept="EvidenceRecord",
                canonical_owner="core.evidence",
                legacy_owners=("core.evidence",),
            )

    def test_dependency_self_edge_is_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            DependencyEdge(source="core.evidence", target="core.evidence")

    def test_migration_steps_are_sorted(self) -> None:
        plan = MigrationPlan(
            plan_id="evidence-canonicalization",
            subject="core.reasoning.evidence",
            target_owner="core.evidence",
            status=MigrationStatus.PLANNED,
            steps=(
                MigrationStep(order=2, step_id="verify", description="Verify"),
                MigrationStep(order=1, step_id="audit", description="Audit"),
            ),
        )
        self.assertEqual([step.order for step in plan.steps], [1, 2])

    def test_duplicate_migration_orders_are_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            MigrationPlan(
                plan_id="invalid",
                subject="legacy",
                target_owner="canonical",
                status=MigrationStatus.PLANNED,
                steps=(
                    MigrationStep(order=1, step_id="a", description="A"),
                    MigrationStep(order=1, step_id="b", description="B"),
                ),
            )

    def test_passed_certification_cannot_have_failures(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            CertificationRecord(
                release_id="genesis-v-a1",
                status=CertificationStatus.PASSED,
                checks_passed=10,
                checks_failed=1,
            )

    def test_snapshot_serializes_and_fingerprints(self) -> None:
        snapshot = ArchitectureSnapshot(
            snapshot_id="fixture",
            repository_root="/repo",
            branch="feature/test",
            commit="abc123",
            modules=(
                ModuleDefinition(
                    path="core/evidence/contracts.py",
                    module="core.evidence.contracts",
                    line_count=50,
                    symbols=(
                        PublicSymbol(
                            name="EvidenceRecord",
                            qualified_name="core.evidence.EvidenceRecord",
                            kind=SymbolKind.CLASS,
                            module="core.evidence.contracts",
                            exported=True,
                        ),
                    ),
                ),
            ),
            ownership=(
                OwnershipDeclaration(
                    concept="EvidenceRecord",
                    canonical_owner="core.evidence",
                    status=OwnershipStatus.CANONICAL,
                ),
            ),
            findings=(
                ArchitectureFinding(
                    finding_id="duplicate-evidence-record",
                    category=FindingCategory.DUPLICATION,
                    severity=FindingSeverity.WARNING,
                    title="Duplicate EvidenceRecord",
                    description="A legacy duplicate remains.",
                ),
            ),
        )
        payload = json.loads(snapshot.to_canonical_json())
        self.assertEqual(payload["snapshot_id"], "fixture")
        self.assertEqual(len(snapshot.fingerprint()), 64)

    def test_file_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.txt"
            path.write_text("architecture\n", encoding="utf-8")
            self.assertEqual(file_fingerprint(path), file_fingerprint(path))

    def test_canonicalize_rejects_unsupported_type(self) -> None:
        with self.assertRaises(Exception):
            canonicalize(object())


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_5a1_architecture_foundation.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify Genesis V-A1 Architecture Intelligence Foundation."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ROOT / "core" / "architecture" / "__init__.py",
    ROOT / "core" / "architecture" / "contracts.py",
    ROOT / "core" / "architecture" / "enums.py",
    ROOT / "core" / "architecture" / "errors.py",
    ROOT / "core" / "architecture" / "fingerprints.py",
    ROOT / "docs" / "architecture" / "architecture_intelligence.md",
    ROOT / "tests" / "test_genesis_5a1_architecture_foundation.py",
)

REQUIRED_EXPORTS = {
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
    "SubsystemDefinition",
    "architecture_fingerprint",
    "canonical_json",
    "canonicalize",
    "file_fingerprint",
}


def check(condition: bool, label: str) -> int:
    if condition:
        print(f"[PASS] {label}")
        return 0
    print(f"[FAIL] {label}")
    return 1


def parse_exports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    return {
                        element.value
                        for element in node.value.elts
                        if isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                    }
    return set()


def main() -> int:
    failures = 0

    failures += check(
        all(path.is_file() for path in REQUIRED_FILES),
        "Required Architecture Intelligence files",
    )

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/architecture",
            "tests/test_genesis_5a1_architecture_foundation.py",
            "dev/verification/verify_genesis_5a1_architecture_foundation.py",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(compile_result.returncode == 0, "Package compilation")

    exports = parse_exports(ROOT / "core" / "architecture" / "__init__.py")
    failures += check(
        REQUIRED_EXPORTS.issubset(exports),
        "Stable public Architecture Intelligence exports",
    )

    contracts_text = (
        ROOT / "core" / "architecture" / "contracts.py"
    ).read_text(encoding="utf-8")
    fingerprints_text = (
        ROOT / "core" / "architecture" / "fingerprints.py"
    ).read_text(encoding="utf-8")

    failures += check(
        "@dataclass(frozen=True, slots=True)" in contracts_text,
        "Immutable slotted architecture contracts",
    )
    failures += check(
        "dataclasses.asdict" not in fingerprints_text,
        "Canonical serializer avoids dataclasses.asdict",
    )
    failures += check(
        "subprocess" not in contracts_text
        and "git " not in contracts_text.lower()
        and "os.system" not in contracts_text,
        "Domain contracts contain no repository side effects",
    )

    test_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5a1_architecture_foundation",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(test_result.returncode == 0, "Genesis V-A1 unit tests")

    smoke_code = """
from core.architecture import (
    ArchitectureSnapshot,
    ModuleDefinition,
    architecture_fingerprint,
)

snapshot = ArchitectureSnapshot(
    snapshot_id="smoke",
    repository_root="/repo",
    branch="feature/test",
    commit="abc123",
    modules=(
        ModuleDefinition(
            path="core/example.py",
            module="core.example",
            line_count=1,
        ),
    ),
)
first = snapshot.fingerprint()
second = snapshot.fingerprint()
assert first == second
assert first == architecture_fingerprint(snapshot)
print(first)
"""
    first_smoke = subprocess.run(
        [sys.executable, "-c", smoke_code],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    second_smoke = subprocess.run(
        [sys.executable, "-c", smoke_code],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    failures += check(
        first_smoke.returncode == 0
        and second_smoke.returncode == 0
        and first_smoke.stdout.strip() == second_smoke.stdout.strip(),
        "Deterministic architecture fingerprint smoke test",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5a1.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-A1 — ARCHITECTURE INTELLIGENCE FOUNDATION"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_5a1_architecture_foundation.py
SHEOF

chmod +x \
    dev/verify_genesis_5a1.sh \
    dev/verification/verify_genesis_5a1_architecture_foundation.py

"${PYTHON_BIN}" dev/verification/verify_genesis_5a1_architecture_foundation.py

echo
echo "Genesis V-A1 Architecture Intelligence Foundation installed."
