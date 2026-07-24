"""Normalized commander-facing readiness contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class ReadinessLevel(str, Enum):
    GOOD = "good"
    CAUTION = "caution"
    BAD = "bad"

class ReadinessColor(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

@dataclass(frozen=True)
class ExecutiveReadiness:
    capability_id: str
    display_name: str
    level: ReadinessLevel
    color: ReadinessColor
    ready: bool
    summary: str
    source_status: str
    checked_at: datetime
    details: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "display_name": self.display_name,
            "level": self.level.value,
            "color": self.color.value,
            "ready": self.ready,
            "summary": self.summary,
            "source_status": self.source_status,
            "checked_at": iso_z(self.checked_at),
            "details": dict(self.details),
        }

_DISPLAY_NAMES = {
    "knowledge": "Knowledge", "reasoning": "Reasoning", "cognition": "Cognition",
    "operations": "Operations", "capabilities": "Capabilities", "executive": "Executive",
    "acquisition": "Acquisition", "observation": "Observation",
}

def normalize_projection_readiness(projection_id: str, projection: Mapping[str, Any]) -> ExecutiveReadiness:
    health = projection.get("health") or {}
    if hasattr(health, "to_dict"):
        health = health.to_dict()
    if not isinstance(health, Mapping):
        health = {}
    status = str(health.get("status") or projection.get("status") or "unknown").strip().lower()
    summary = str(health.get("summary") or projection.get("summary") or "Readiness is unknown.")
    details = health.get("details") or {}
    if hasattr(details, "to_dict"):
        details = details.to_dict()
    if not isinstance(details, Mapping):
        details = {}
    warnings = health.get("warnings") or projection.get("warnings") or []
    errors = health.get("errors") or projection.get("errors") or []
    if status in {"available", "healthy", "ready", "operational"}:
        if errors:
            level, color, ready = ReadinessLevel.BAD, ReadinessColor.RED, False
        elif warnings:
            level, color, ready = ReadinessLevel.CAUTION, ReadinessColor.YELLOW, True
        else:
            level, color, ready = ReadinessLevel.GOOD, ReadinessColor.GREEN, True
    elif status in {"degraded", "partial", "caution", "warning"}:
        level, color, ready = ReadinessLevel.CAUTION, ReadinessColor.YELLOW, True
    else:
        level, color, ready = ReadinessLevel.BAD, ReadinessColor.RED, False
    return ExecutiveReadiness(
        capability_id=projection_id,
        display_name=_DISPLAY_NAMES.get(projection_id, projection_id.replace("_", " ").title()),
        level=level, color=color, ready=ready, summary=summary, source_status=status,
        checked_at=utc_now(),
        details={**dict(details), "warning_count": len(warnings), "error_count": len(errors)},
    )
