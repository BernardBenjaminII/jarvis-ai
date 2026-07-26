"""Canonical Observation public API.

This module preserves the historical IV-B3 and IV-B4 public surface while
exposing the final deterministic Observation convergence architecture.
"""

from __future__ import annotations

from .adapters import (
    adapt_cognition_common_observation,
    adapt_cognition_observation,
    adapt_executive_observation,
    adapt_legacy_observation,
    adapt_operational_observation,
    adapt_registered_observation,
    adapt_representation_observation,
)
from .audit import (
    AUDIT_SCHEMA_VERSION,
    ObservationConvergenceReport,
    ObservationDefinition,
    ObservationDefinitionStatus,
    audit_observation_definitions,
    format_observation_convergence_report,
    render_observation_convergence_markdown,
    require_observation_convergence,
    write_observation_convergence_reports,
)
from .compatibility import (
    CompatibilityReceipt,
    LegacyObservationCompatibilityWarning,
    canonicalize_observation,
)
from .contracts import *
from .enums import *
from .errors import *
from .export_audit import (
    ObservationExport,
    module_defines_observation,
    scan_observation_exports,
)
from .migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MIGRATION_ENTRIES,
    MIGRATION_SCHEMA_VERSION,
    OBSERVATION_MIGRATION_REGISTRY,
    MigrationDisposition,
    MigrationReadiness,
    ObservationMigrationEntry,
    approved_legacy_entries,
    canonical_observation_entry,
    deprecated_rename_entries,
    migration_entries,
    migration_entry_for,
    migration_entry_for_path,
    migration_registry_fingerprint,
    migration_registry_payload,
)
from .serialization import *


_EXPLICIT_EXPORTS = {
    "AUDIT_SCHEMA_VERSION",
    "CANONICAL_OBSERVATION_PATH",
    "CompatibilityReceipt",
    "LegacyObservationCompatibilityWarning",
    "MIGRATION_ENTRIES",
    "MIGRATION_SCHEMA_VERSION",
    "OBSERVATION_MIGRATION_REGISTRY",
    "MigrationDisposition",
    "MigrationReadiness",
    "ObservationConvergenceReport",
    "ObservationDefinition",
    "ObservationDefinitionStatus",
    "ObservationExport",
    "ObservationMigrationEntry",
    "adapt_cognition_common_observation",
    "adapt_cognition_observation",
    "adapt_executive_observation",
    "adapt_legacy_observation",
    "adapt_operational_observation",
    "adapt_registered_observation",
    "adapt_representation_observation",
    "approved_legacy_entries",
    "audit_observation_definitions",
    "canonical_observation_entry",
    "canonicalize_observation",
    "deprecated_rename_entries",
    "format_observation_convergence_report",
    "migration_entries",
    "migration_entry_for",
    "migration_entry_for_path",
    "migration_registry_fingerprint",
    "migration_registry_payload",
    "module_defines_observation",
    "render_observation_convergence_markdown",
    "require_observation_convergence",
    "scan_observation_exports",
    "write_observation_convergence_reports",
}


__all__ = sorted(
    name
    for name in globals()
    if not name.startswith("_")
    and (
        name in _EXPLICIT_EXPORTS
        or getattr(
            globals()[name],
            "__module__",
            "",
        ).startswith("core.observation")
    )
)
