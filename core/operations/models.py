"""Immutable snapshot models for the JARVIS Operations interface."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from .enums import (
    ActivityState,
    AlertSeverity,
    HealthState,
    MissionState,
    ObjectiveState,
    OperationalState,
)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    return value


class SerializableSnapshot:
    """Mixin for stable JSON-compatible snapshot conversion."""

    def to_dict(self) -> dict[str, Any]:
        result = _serialize(self)
        if not isinstance(result, dict):
            raise TypeError("snapshot serialization did not produce a mapping")
        return result


@dataclass(frozen=True, slots=True)
class Provenance(SerializableSnapshot):
    source: str
    source_version: str
    captured_at: datetime


@dataclass(frozen=True, slots=True)
class ActivitySnapshot(SerializableSnapshot):
    activity_id: str
    name: str
    state: ActivityState
    updated_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class ObjectiveSnapshot(SerializableSnapshot):
    objective_id: str
    name: str
    state: ObjectiveState
    activities: tuple[ActivitySnapshot, ...]
    updated_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class MissionSnapshot(SerializableSnapshot):
    mission_id: str
    name: str
    state: MissionState
    objectives: tuple[ObjectiveSnapshot, ...]
    created_at: datetime
    updated_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class HealthComponentSnapshot(SerializableSnapshot):
    component: str
    state: HealthState
    detail: str
    checked_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class HealthSnapshot(SerializableSnapshot):
    state: HealthState
    components: tuple[HealthComponentSnapshot, ...]
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class ResourceSnapshot(SerializableSnapshot):
    cpu_percent: float | None
    memory_percent: float | None
    disk_percent: float | None
    load_average_1m: float | None
    queue_depth: int
    mission_count: int
    worker_count: int
    measured_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class TimelineEntrySnapshot(SerializableSnapshot):
    event_id: str
    event_kind: str
    occurred_at: datetime
    summary: str
    subject_id: str | None
    payload: Mapping[str, Any]
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class TimelineSnapshot(SerializableSnapshot):
    entries: tuple[TimelineEntrySnapshot, ...]
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class AlertSnapshot(SerializableSnapshot):
    alert_id: str
    severity: AlertSeverity
    title: str
    detail: str
    active: bool
    raised_at: datetime
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class OperationsSnapshot(SerializableSnapshot):
    state: OperationalState
    missions: tuple[MissionSnapshot, ...]
    health: HealthSnapshot
    resources: ResourceSnapshot
    timeline: TimelineSnapshot
    alerts: tuple[AlertSnapshot, ...]
    generated_at: datetime
    fingerprint: str
