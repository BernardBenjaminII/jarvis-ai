"""
Immutable contracts for JARVIS Phase VII-B2 persistent source registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from knowledge_engine.acquisition_control import NormalizedSource


class SourceLifecycleState(str, Enum):
    ADMITTED = "admitted"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class RegisteredSource:
    registry_id: int
    source_id: str
    display_name: str
    canonical_location: str
    kind: str
    trust_tier: str
    fingerprint: str
    host: str | None
    lifecycle_state: SourceLifecycleState
    admitted_at: str
    updated_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata or {})),
        )


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    source: RegisteredSource
    created: bool


@dataclass(frozen=True, slots=True)
class RegistryStats:
    total: int
    admitted: int
    active: int
    paused: int
    retired: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalized_to_record(
    registry_id: int,
    source: NormalizedSource,
    lifecycle_state: SourceLifecycleState,
    admitted_at: str,
    updated_at: str,
) -> RegisteredSource:
    return RegisteredSource(
        registry_id=registry_id,
        source_id=source.source_id,
        display_name=source.display_name,
        canonical_location=source.canonical_location,
        kind=source.kind.value,
        trust_tier=source.trust_tier.value,
        fingerprint=source.fingerprint,
        host=source.host,
        lifecycle_state=lifecycle_state,
        admitted_at=admitted_at,
        updated_at=updated_at,
        metadata=source.metadata,
    )
