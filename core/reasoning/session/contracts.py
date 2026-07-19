"""Immutable contracts for managed reasoning sessions.

Genesis II-A1 deliberately defines data contracts without introducing session
execution, lifecycle mutation, persistence, or executive authority.

The certified ReasoningEngine remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from uuid import UUID, uuid5


class ReasoningSessionState(str, Enum):
    """Canonical vocabulary for reasoning-session lifecycle states.

    Genesis II-A1 defines the vocabulary only. Valid transitions are governed
    by the lifecycle policy introduced in Genesis II-A2.
    """

    CREATED = "created"
    INITIALIZED = "initialized"
    COLLECTING_EVIDENCE = "collecting_evidence"
    REASONING = "reasoning"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True, order=True)
class SessionAttribute:
    """A deterministic metadata attribute."""

    key: str
    value: str

    def __post_init__(self) -> None:
        key = self.key.strip()
        value = self.value.strip()

        if not key:
            raise ValueError("SessionAttribute.key must not be blank.")

        object.__setattr__(self, "key", key)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True, order=True)
class ReasoningSessionId:
    """Stable identifier for a managed reasoning session."""

    value: str

    def __post_init__(self) -> None:
        normalized = str(UUID(self.value))
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: str | UUID) -> "ReasoningSessionId":
        """Create an identifier from an existing UUID value."""

        return cls(str(value))

    @classmethod
    def derive(
        cls,
        *,
        namespace: str | UUID,
        material: str,
    ) -> "ReasoningSessionId":
        """Derive a stable identifier using UUIDv5."""

        normalized_material = material.strip()
        if not normalized_material:
            raise ValueError("ReasoningSessionId material must not be blank.")

        namespace_uuid = namespace if isinstance(namespace, UUID) else UUID(namespace)
        return cls(str(uuid5(namespace_uuid, normalized_material)))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReasoningSessionMetadata:
    """Immutable executive context attached to a reasoning session."""

    created_by: str
    mission_id: str | None = None
    objective_id: str | None = None
    correlation_id: str | None = None
    attributes: tuple[SessionAttribute, ...] = field(default_factory=tuple)
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        created_by = self.created_by.strip()
        if not created_by:
            raise ValueError("ReasoningSessionMetadata.created_by must not be blank.")

        mission_id = self._normalize_optional(self.mission_id)
        objective_id = self._normalize_optional(self.objective_id)
        correlation_id = self._normalize_optional(self.correlation_id)
        schema_version = self.schema_version.strip()

        if not schema_version:
            raise ValueError(
                "ReasoningSessionMetadata.schema_version must not be blank."
            )

        attributes = self._normalize_attributes(self.attributes)

        object.__setattr__(self, "created_by", created_by)
        object.__setattr__(self, "mission_id", mission_id)
        object.__setattr__(self, "objective_id", objective_id)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "attributes", attributes)
        object.__setattr__(self, "schema_version", schema_version)

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_attributes(
        attributes: Iterable[SessionAttribute],
    ) -> tuple[SessionAttribute, ...]:
        normalized = tuple(sorted(tuple(attributes), key=lambda item: item.key))

        keys = [attribute.key for attribute in normalized]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "ReasoningSessionMetadata.attributes must contain unique keys."
            )

        return normalized


@dataclass(frozen=True, slots=True)
class ReasoningSession:
    """Constitutional snapshot of a managed reasoning session."""

    session_id: ReasoningSessionId
    metadata: ReasoningSessionMetadata
    state: ReasoningSessionState = ReasoningSessionState.CREATED
    revision: int = 0

    def __post_init__(self) -> None:
        if self.revision < 0:
            raise ValueError("ReasoningSession.revision must be non-negative.")
