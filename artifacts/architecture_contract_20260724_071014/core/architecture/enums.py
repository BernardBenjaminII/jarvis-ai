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
