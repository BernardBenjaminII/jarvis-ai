"""Canonical Observation migration registry.

Genesis IV-B4 Final Convergence establishes this module as the single source
of truth for Observation-definition ownership and migration disposition.

The module preserves the historical IV-B4 public API while exposing the
deterministic IV-B4C registry API.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Final, Iterable


MIGRATION_SCHEMA_VERSION: Final[str] = (
    "jarvis.observation-migration-registry.v3"
)
CANONICAL_OBSERVATION_PATH: Final[str] = (
    "core/observation/contracts.py"
)


class MigrationDisposition(str, Enum):
    """Governance disposition for a known Observation definition."""

    CANONICAL = "canonical"
    APPROVED_LEGACY = "approved_legacy"
    DEPRECATED_RENAME = "deprecated_rename"
    FORBIDDEN = "forbidden"


class MigrationReadiness(str, Enum):
    """Readiness of a definition for controlled migration."""

    NOT_REQUIRED = "not_required"
    ADAPTER_AVAILABLE = "adapter_available"
    RENAME_PLANNED = "rename_planned"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ObservationMigrationEntry:
    """Deterministic governance record for an Observation definition."""

    path: str
    semantic_role: str
    disposition: MigrationDisposition
    readiness: MigrationReadiness
    canonical_adapter: str | None
    target_name: str | None
    rationale: str

    def canonical_payload(self) -> dict[str, str | None]:
        return {
            "path": self.path,
            "semantic_role": self.semantic_role,
            "disposition": self.disposition.value,
            "readiness": self.readiness.value,
            "canonical_adapter": self.canonical_adapter,
            "target_name": self.target_name,
            "rationale": self.rationale,
        }


OBSERVATION_MIGRATION_REGISTRY: tuple[
    ObservationMigrationEntry, ...
] = (
    ObservationMigrationEntry(
        path=CANONICAL_OBSERVATION_PATH,
        semantic_role="canonical_observation_contract",
        disposition=MigrationDisposition.CANONICAL,
        readiness=MigrationReadiness.NOT_REQUIRED,
        canonical_adapter=None,
        target_name="Observation",
        rationale=(
            "Canonical immutable Observation contract owned by the "
            "Observation subsystem."
        ),
    ),
    ObservationMigrationEntry(
        path="core/cognition/common/contracts.py",
        semantic_role="legacy_cognition_fact",
        disposition=MigrationDisposition.APPROVED_LEGACY,
        readiness=MigrationReadiness.ADAPTER_AVAILABLE,
        canonical_adapter=(
            "core.observation.adapters:"
            "adapt_cognition_common_observation"
        ),
        target_name=None,
        rationale=(
            "Historical cognition-domain fact contract retained temporarily "
            "for compatibility while consumers migrate."
        ),
    ),
    ObservationMigrationEntry(
        path="core/cognition/observation/models.py",
        semantic_role="operational_observation_record",
        disposition=MigrationDisposition.DEPRECATED_RENAME,
        readiness=MigrationReadiness.RENAME_PLANNED,
        canonical_adapter=(
            "core.observation.adapters:"
            "adapt_operational_observation"
        ),
        target_name="ObservationRecord",
        rationale=(
            "Operational runtime record whose semantics differ from the "
            "canonical Observation contract."
        ),
    ),
    ObservationMigrationEntry(
        path="core/representation/contracts.py",
        semantic_role="represented_statement",
        disposition=MigrationDisposition.DEPRECATED_RENAME,
        readiness=MigrationReadiness.RENAME_PLANNED,
        canonical_adapter=(
            "core.observation.adapters:"
            "adapt_representation_observation"
        ),
        target_name="RepresentedStatement",
        rationale=(
            "Cognitive representation object whose semantics differ from "
            "canonical Observation."
        ),
    ),
)


def _validate_registry(
    entries: Iterable[ObservationMigrationEntry],
) -> tuple[ObservationMigrationEntry, ...]:
    normalized = tuple(entries)

    paths = [entry.path for entry in normalized]
    if len(paths) != len(set(paths)):
        raise ValueError(
            "Observation migration registry paths must be unique"
        )

    canonical = tuple(
        entry
        for entry in normalized
        if entry.disposition is MigrationDisposition.CANONICAL
    )
    if len(canonical) != 1:
        raise ValueError(
            "Observation migration registry must contain exactly one "
            "canonical owner"
        )
    if canonical[0].path != CANONICAL_OBSERVATION_PATH:
        raise ValueError(
            "Canonical Observation owner does not match declared path"
        )

    for entry in normalized:
        if entry.disposition is MigrationDisposition.CANONICAL:
            if entry.readiness is not MigrationReadiness.NOT_REQUIRED:
                raise ValueError(
                    "Canonical Observation must not require migration"
                )
            if entry.canonical_adapter is not None:
                raise ValueError(
                    "Canonical Observation must not declare an adapter"
                )

        elif entry.disposition is MigrationDisposition.APPROVED_LEGACY:
            if entry.readiness is not MigrationReadiness.ADAPTER_AVAILABLE:
                raise ValueError(
                    "Approved legacy Observation must have an adapter"
                )
            if not entry.canonical_adapter:
                raise ValueError(
                    "Approved legacy Observation adapter is required"
                )

        elif entry.disposition is MigrationDisposition.DEPRECATED_RENAME:
            if entry.readiness is not MigrationReadiness.RENAME_PLANNED:
                raise ValueError(
                    "Deprecated Observation must have rename planning"
                )
            if not entry.target_name:
                raise ValueError(
                    "Deprecated Observation must declare a target name"
                )
            if not entry.canonical_adapter:
                raise ValueError(
                    "Deprecated Observation must retain an adapter"
                )

    return normalized


OBSERVATION_MIGRATION_REGISTRY = _validate_registry(
    OBSERVATION_MIGRATION_REGISTRY
)

# Historical IV-B4 compatibility alias.
MIGRATION_ENTRIES = OBSERVATION_MIGRATION_REGISTRY


def migration_entries() -> tuple[ObservationMigrationEntry, ...]:
    """Return the complete deterministic registry."""

    return OBSERVATION_MIGRATION_REGISTRY


def migration_entry_for(
    path: str,
) -> ObservationMigrationEntry | None:
    """Return the registry entry for a repository-relative path."""

    normalized = str(path).replace("\\", "/")
    for entry in OBSERVATION_MIGRATION_REGISTRY:
        if entry.path == normalized:
            return entry
    return None


def migration_entry_for_path(
    path: str,
) -> ObservationMigrationEntry | None:
    """Historical IV-B4 compatibility wrapper."""

    return migration_entry_for(path)


def migration_registry_payload() -> dict[str, object]:
    """Return the canonical serializable registry payload."""

    entries = tuple(
        entry.canonical_payload()
        for entry in sorted(
            OBSERVATION_MIGRATION_REGISTRY,
            key=lambda item: item.path,
        )
    )
    return {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "canonical_path": CANONICAL_OBSERVATION_PATH,
        "entries": entries,
    }


def migration_registry_fingerprint() -> str:
    """Return a deterministic SHA-256 fingerprint of the registry."""

    encoded = json.dumps(
        migration_registry_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_observation_entry() -> ObservationMigrationEntry:
    """Return the sole canonical Observation owner."""

    entry = migration_entry_for(CANONICAL_OBSERVATION_PATH)
    if entry is None:
        raise RuntimeError(
            "canonical Observation registry entry is missing"
        )
    return entry


def approved_legacy_entries() -> tuple[
    ObservationMigrationEntry, ...
]:
    return tuple(
        entry
        for entry in OBSERVATION_MIGRATION_REGISTRY
        if entry.disposition is MigrationDisposition.APPROVED_LEGACY
    )


def deprecated_rename_entries() -> tuple[
    ObservationMigrationEntry, ...
]:
    return tuple(
        entry
        for entry in OBSERVATION_MIGRATION_REGISTRY
        if entry.disposition is MigrationDisposition.DEPRECATED_RENAME
    )


__all__ = [
    "CANONICAL_OBSERVATION_PATH",
    "MIGRATION_ENTRIES",
    "MIGRATION_SCHEMA_VERSION",
    "MigrationDisposition",
    "MigrationReadiness",
    "OBSERVATION_MIGRATION_REGISTRY",
    "ObservationMigrationEntry",
    "approved_legacy_entries",
    "canonical_observation_entry",
    "deprecated_rename_entries",
    "migration_entries",
    "migration_entry_for",
    "migration_entry_for_path",
    "migration_registry_fingerprint",
    "migration_registry_payload",
]
