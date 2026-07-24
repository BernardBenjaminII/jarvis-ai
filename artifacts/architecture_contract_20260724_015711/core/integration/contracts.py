"""Stable contracts for the Executive Integration Plane."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class ProjectionStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    NOT_CONFIGURED = "not_configured"

@dataclass(frozen=True)
class ProjectionHealth:
    status: ProjectionStatus
    summary: str
    checked_at: datetime = field(default_factory=utc_now)
    details: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "summary": self.summary,
            "checked_at": isoformat_utc(self.checked_at),
            "details": dict(self.details),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

@dataclass(frozen=True)
class ProjectionEnvelope:
    projection_id: str
    schema_version: str
    generated_at: datetime
    health: ProjectionHealth
    data: dict[str, Any]
    provider: str
    source_timestamp: datetime | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "schema_version": self.schema_version,
            "generated_at": isoformat_utc(self.generated_at),
            "source_timestamp": isoformat_utc(self.source_timestamp) if self.source_timestamp else None,
            "provider": self.provider,
            "health": self.health.to_dict(),
            "data": dict(self.data),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
