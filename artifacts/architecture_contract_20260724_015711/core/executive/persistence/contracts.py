"""Durable persistence contracts for Genesis VI-A6.1.

This module defines the immutable vocabulary used by later persistence
milestones. It deliberately performs no file I/O and owns no storage backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple


PERSISTENCE_SCHEMA_NAME = "jarvis.executive.persistence"
PERSISTENCE_SCHEMA_VERSION = 1
DIGEST_ALGORITHM = "sha256"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return an immutable mapping with deterministic key ordering."""

    if not value:
        return MappingProxyType({})

    ordered = {
        str(key): value[key]
        for key in sorted(value, key=lambda item: str(item))
    }
    return MappingProxyType(ordered)


class PersistenceRecordKind(str, Enum):
    """Kinds of durable executive records."""

    SESSION_SNAPSHOT = "session_snapshot"
    CHECKPOINT = "checkpoint"
    REPLAY_FRAME = "replay_frame"
    MIGRATION_RECORD = "migration_record"


class PersistenceIntegrityStatus(str, Enum):
    """Integrity disposition for a durable record."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    INVALID = "invalid"


class CheckpointReason(str, Enum):
    """Why an executive checkpoint was requested."""

    MANUAL = "manual"
    PERIODIC = "periodic"
    STATE_TRANSITION = "state_transition"
    SUSPENSION = "suspension"
    COMPLETION = "completion"
    FAILURE = "failure"
    SHUTDOWN = "shutdown"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True, order=True)
class SchemaIdentity:
    """Stable identity of one persistence schema revision."""

    name: str = PERSISTENCE_SCHEMA_NAME
    version: int = PERSISTENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("schema name must not be empty")
        if self.version < 1:
            raise ValueError("schema version must be at least 1")

    @property
    def canonical(self) -> str:
        """Return the canonical schema identifier."""

        return f"{self.name}@{self.version}"


@dataclass(frozen=True, slots=True)
class IntegrityMetadata:
    """Digest information carried beside a durable payload."""

    algorithm: str
    digest: str
    status: PersistenceIntegrityStatus = (
        PersistenceIntegrityStatus.UNVERIFIED
    )

    def __post_init__(self) -> None:
        algorithm = self.algorithm.strip().lower()
        digest = self.digest.strip().lower()

        if algorithm != DIGEST_ALGORITHM:
            raise ValueError(
                f"unsupported integrity algorithm: {self.algorithm}"
            )
        if len(digest) != 64:
            raise ValueError("sha256 digest must contain 64 hexadecimal characters")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError("sha256 digest must be hexadecimal") from exc

        object.__setattr__(self, "algorithm", algorithm)
        object.__setattr__(self, "digest", digest)


@dataclass(frozen=True, slots=True)
class PersistenceEnvelope:
    """Immutable metadata envelope around one serialized payload."""

    record_id: str
    record_kind: PersistenceRecordKind
    schema: SchemaIdentity
    session_id: str
    mission_id: str
    executive_id: str
    created_at: datetime
    payload_size: int
    integrity: IntegrityMetadata
    parent_record_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (
            ("record_id", self.record_id),
            ("session_id", self.session_id),
            ("mission_id", self.mission_id),
            ("executive_id", self.executive_id),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.payload_size < 0:
            raise ValueError("payload_size must not be negative")
        if (
            self.parent_record_id is not None
            and not self.parent_record_id.strip()
        ):
            raise ValueError("parent_record_id must not be blank")

        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class CheckpointDescriptor:
    """Immutable description of one executive checkpoint."""

    checkpoint_id: str
    session_id: str
    sequence: int
    reason: CheckpointReason
    record_id: str
    created_at: datetime
    previous_checkpoint_id: str | None = None
    tags: Tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (
            ("checkpoint_id", self.checkpoint_id),
            ("session_id", self.session_id),
            ("record_id", self.record_id),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")

        if self.sequence < 1:
            raise ValueError("sequence must be at least 1")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if (
            self.previous_checkpoint_id is not None
            and not self.previous_checkpoint_id.strip()
        ):
            raise ValueError("previous_checkpoint_id must not be blank")

        normalized_tags = tuple(
            sorted(
                {
                    tag.strip()
                    for tag in self.tags
                    if tag.strip()
                }
            )
        )
        object.__setattr__(self, "tags", normalized_tags)
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class MigrationPath:
    """Declared schema migration boundary.

    VI-A6.1 defines migration contracts only. Migration execution belongs to a
    later VI-A6 milestone.
    """

    schema_name: str
    source_version: int
    target_version: int
    migration_id: str

    def __post_init__(self) -> None:
        if not self.schema_name.strip():
            raise ValueError("schema_name must not be empty")
        if not self.migration_id.strip():
            raise ValueError("migration_id must not be empty")
        if self.source_version < 1:
            raise ValueError("source_version must be at least 1")
        if self.target_version <= self.source_version:
            raise ValueError(
                "target_version must be greater than source_version"
            )

    @property
    def source(self) -> SchemaIdentity:
        return SchemaIdentity(self.schema_name, self.source_version)

    @property
    def target(self) -> SchemaIdentity:
        return SchemaIdentity(self.schema_name, self.target_version)


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    """Immutable request to recover an executive session."""

    session_id: str
    checkpoint_id: str | None = None
    require_verified_integrity: bool = True
    allow_migration: bool = False
    target_schema: SchemaIdentity = field(
        default_factory=SchemaIdentity
    )

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")
        if self.checkpoint_id is not None and not self.checkpoint_id.strip():
            raise ValueError("checkpoint_id must not be blank")


__all__ = [
    "CheckpointDescriptor",
    "CheckpointReason",
    "DIGEST_ALGORITHM",
    "IntegrityMetadata",
    "MigrationPath",
    "PERSISTENCE_SCHEMA_NAME",
    "PERSISTENCE_SCHEMA_VERSION",
    "PersistenceEnvelope",
    "PersistenceIntegrityStatus",
    "PersistenceRecordKind",
    "RecoveryRequest",
    "SchemaIdentity",
    "freeze_mapping",
    "utc_now",
]
