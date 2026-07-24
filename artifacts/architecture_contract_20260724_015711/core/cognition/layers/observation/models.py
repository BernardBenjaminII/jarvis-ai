from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4

from core.cognition.common.object_model import ProvenanceReference

from .enums import (
    ObservationLifecycleState,
    ObservationRelationType,
    ObservationSourceMode,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _freeze(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def _canonicalize(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, ProvenanceReference):
        return value.to_primitive()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported canonical value: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class ObservationInput:
    content: str
    source_mode: ObservationSourceMode
    provenance: tuple[ProvenanceReference, ...]
    confidence: float = 1.0
    observed_at: datetime = field(default_factory=utc_now)
    authority: str | None = None
    subject: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "attributes", _freeze(self.attributes))


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    observation_id: UUID
    content: str
    normalized_content: str
    source_mode: ObservationSourceMode
    provenance: tuple[ProvenanceReference, ...]
    confidence: float
    observed_at: datetime
    created_at: datetime
    lifecycle_state: ObservationLifecycleState
    authority: str | None = None
    subject: str | None = None
    supersedes_id: UUID | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("observed_at", "created_at"):
            value = getattr(self, name)
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
            object.__setattr__(self, name, value.astimezone(timezone.utc))
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "attributes", _freeze(self.attributes))

    def to_primitive(self) -> dict[str, Any]:
        return {
            "observation_id": str(self.observation_id),
            "content": self.content,
            "normalized_content": self.normalized_content,
            "source_mode": self.source_mode.value,
            "provenance": [item.to_primitive() for item in self.provenance],
            "confidence": self.confidence,
            "observed_at": self.observed_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "lifecycle_state": self.lifecycle_state.value,
            "authority": self.authority,
            "subject": self.subject,
            "supersedes_id": (
                str(self.supersedes_id) if self.supersedes_id is not None else None
            ),
            "attributes": _canonicalize(self.attributes),
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_primitive(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @property
    def deterministic_hash(self) -> str:
        return hashlib.sha256(
            self.to_canonical_json().encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ObservationRelation:
    source_id: UUID
    target_id: UUID
    relation_type: ObservationRelationType
    confidence: float = 1.0
    created_at: datetime = field(default_factory=utc_now)
    rationale: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationValidationIssue:
    code: str
    message: str
    field_name: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationValidationResult:
    valid: bool
    issues: tuple[ObservationValidationIssue, ...] = ()


__all__ = (
    "ObservationInput",
    "ObservationRecord",
    "ObservationRelation",
    "ObservationValidationIssue",
    "ObservationValidationResult",
    "utc_now",
)
