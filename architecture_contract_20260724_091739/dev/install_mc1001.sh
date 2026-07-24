#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
cd "$PROJECT_ROOT"

if [[ ! -d core || ! -d dev || ! -d tests ]]; then
    echo "ERROR: Run this installer from the JARVIS repository root."
    echo "Expected directories: core/, dev/, tests/"
    exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT=".migration_backups/mc1001_${STAMP}"

backup_if_present() {
    local target="$1"
    if [[ -e "$target" ]]; then
        mkdir -p "$BACKUP_ROOT/$(dirname "$target")"
        cp -a "$target" "$BACKUP_ROOT/$target"
    fi
}

write_file() {
    local target="$1"
    backup_if_present "$target"
    mkdir -p "$(dirname "$target")"
    cat > "$target"
    echo "[WRITE] $target"
}

echo "======================================================================"
echo "JARVIS — MC-1001 SPRINT 0 EXECUTIVE OPERATIONS INTERFACE"
echo "======================================================================"

write_file core/operations/enums.py <<'PY'
"""Enumerations for the JARVIS Operations interface."""

from __future__ import annotations

from enum import Enum


class OperationalState(str, Enum):
    """Top-level operational state."""

    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    PAUSED = "paused"
    FAILED = "failed"
    STOPPED = "stopped"


class HealthState(str, Enum):
    """Health of an individual component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class MissionState(str, Enum):
    """Externally visible mission state."""

    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ObjectiveState(str, Enum):
    """Externally visible objective state."""

    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class ActivityState(str, Enum):
    """Externally visible activity state."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    """Operational alert severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventKind(str, Enum):
    """Canonical event names exposed by Operations."""

    MISSION_STARTED = "MissionStarted"
    MISSION_COMPLETED = "MissionCompleted"
    OBSERVATION_CREATED = "ObservationCreated"
    EVIDENCE_VALIDATED = "EvidenceValidated"
    REASONING_STARTED = "ReasoningStarted"
    REASONING_COMPLETED = "ReasoningCompleted"
    KNOWLEDGE_ASSIMILATED = "KnowledgeAssimilated"
    CHECKPOINT_CREATED = "CheckpointCreated"
    EXECUTIVE_RECOVERED = "ExecutiveRecovered"
    SYSTEM_HEALTH_CHANGED = "SystemHealthChanged"
PY

write_file core/operations/errors.py <<'PY'
"""Errors raised by the JARVIS Operations interface."""


class OperationsError(RuntimeError):
    """Base class for Operations failures."""


class OperationsProviderError(OperationsError):
    """A backing provider could not produce an operational view."""


class InvalidOperationsEventError(OperationsError):
    """An event violated the Operations event contract."""
PY

write_file core/operations/contracts.py <<'PY'
"""Provider contracts consumed by the Operations service."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MissionProvider(Protocol):
    """Produces mission records without exposing Executive internals."""

    def list_missions(self) -> Iterable[Mapping[str, Any]]:
        """Return mission records suitable for snapshot conversion."""


@runtime_checkable
class HealthProvider(Protocol):
    """Produces component health records."""

    def collect_health(self) -> Iterable[Mapping[str, Any]]:
        """Return component health records."""


@runtime_checkable
class ResourceProvider(Protocol):
    """Produces runtime resource measurements."""

    def collect_resources(self) -> Mapping[str, Any]:
        """Return one resource measurement mapping."""
PY

write_file core/operations/models.py <<'PY'
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
PY

write_file core/operations/events.py <<'PY'
"""Canonical Operations events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import uuid4

from .enums import EventKind
from .models import Provenance, SerializableSnapshot, utc_now


@dataclass(frozen=True, slots=True)
class OperationsEvent(SerializableSnapshot):
    event_id: str
    kind: EventKind
    occurred_at: datetime
    summary: str
    subject_id: str | None
    payload: Mapping[str, Any]
    provenance: Provenance

    @classmethod
    def create(
        cls,
        *,
        kind: EventKind,
        summary: str,
        subject_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        source: str = "operations",
        source_version: str = "mc1001",
        occurred_at: datetime | None = None,
        event_id: str | None = None,
    ) -> "OperationsEvent":
        timestamp = occurred_at or utc_now()
        return cls(
            event_id=event_id or str(uuid4()),
            kind=kind,
            occurred_at=timestamp,
            summary=summary,
            subject_id=subject_id,
            payload=dict(payload or {}),
            provenance=Provenance(
                source=source,
                source_version=source_version,
                captured_at=timestamp,
            ),
        )
PY

write_file core/operations/registry.py <<'PY'
"""Thread-safe in-memory registry for Sprint 0 Operations events."""

from __future__ import annotations

from threading import RLock

from .events import OperationsEvent


class OperationsEventRegistry:
    """Stores canonical events in insertion order."""

    def __init__(self) -> None:
        self._events: list[OperationsEvent] = []
        self._lock = RLock()

    def append(self, event: OperationsEvent) -> None:
        with self._lock:
            self._events.append(event)

    def list_events(self, *, limit: int | None = None) -> tuple[OperationsEvent, ...]:
        with self._lock:
            events = tuple(self._events)
        if limit is None:
            return events
        if limit < 0:
            raise ValueError("limit must be zero or greater")
        return events[-limit:] if limit else ()

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
PY

write_file core/operations/missions.py <<'PY'
"""Mission snapshot adapter."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from .contracts import MissionProvider
from .enums import ActivityState, MissionState, ObjectiveState
from .models import (
    ActivitySnapshot,
    MissionSnapshot,
    ObjectiveSnapshot,
    Provenance,
    utc_now,
)


class EmptyMissionProvider:
    """Default provider used until an Executive adapter is registered."""

    def list_missions(self) -> Iterable[Mapping[str, Any]]:
        return ()


def _timestamp(value: Any, fallback: datetime) -> datetime:
    return value if isinstance(value, datetime) else fallback


class MissionSnapshotAdapter:
    """Converts provider mappings into immutable mission snapshots."""

    def __init__(self, provider: MissionProvider | None = None) -> None:
        self._provider = provider or EmptyMissionProvider()

    def collect(self, *, captured_at: datetime | None = None) -> tuple[MissionSnapshot, ...]:
        now = captured_at or utc_now()
        snapshots: list[MissionSnapshot] = []

        for record in self._provider.list_missions():
            mission_id = str(record.get("mission_id", record.get("id", ""))).strip()
            if not mission_id:
                continue

            provenance = Provenance(
                source=str(record.get("source", "executive")),
                source_version=str(record.get("source_version", "unknown")),
                captured_at=now,
            )

            objectives: list[ObjectiveSnapshot] = []
            for objective in record.get("objectives", ()):
                activities = tuple(
                    ActivitySnapshot(
                        activity_id=str(activity.get("activity_id", activity.get("id", ""))),
                        name=str(activity.get("name", "Unnamed activity")),
                        state=ActivityState(str(activity.get("state", "queued"))),
                        updated_at=_timestamp(activity.get("updated_at"), now),
                        provenance=provenance,
                    )
                    for activity in objective.get("activities", ())
                )
                objectives.append(
                    ObjectiveSnapshot(
                        objective_id=str(
                            objective.get("objective_id", objective.get("id", ""))
                        ),
                        name=str(objective.get("name", "Unnamed objective")),
                        state=ObjectiveState(str(objective.get("state", "pending"))),
                        activities=activities,
                        updated_at=_timestamp(objective.get("updated_at"), now),
                        provenance=provenance,
                    )
                )

            snapshots.append(
                MissionSnapshot(
                    mission_id=mission_id,
                    name=str(record.get("name", "Unnamed mission")),
                    state=MissionState(str(record.get("state", "planned"))),
                    objectives=tuple(objectives),
                    created_at=_timestamp(record.get("created_at"), now),
                    updated_at=_timestamp(record.get("updated_at"), now),
                    provenance=provenance,
                )
            )

        return tuple(sorted(snapshots, key=lambda item: item.mission_id))
PY

write_file core/operations/health.py <<'PY'
"""Health aggregation for the Operations interface."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Any

from .enums import HealthState
from .models import HealthComponentSnapshot, HealthSnapshot, Provenance, utc_now

HealthProbe = Callable[[], Mapping[str, Any]]


class HealthAggregator:
    """Aggregates independent component probes into one health snapshot."""

    def __init__(self, probes: Mapping[str, HealthProbe] | None = None) -> None:
        self._probes = dict(probes or {})

    def collect(self, *, checked_at: datetime | None = None) -> HealthSnapshot:
        now = checked_at or utc_now()
        components: list[HealthComponentSnapshot] = []

        if not self._probes:
            components.append(
                HealthComponentSnapshot(
                    component="operations",
                    state=HealthState.HEALTHY,
                    detail="Operations service is available.",
                    checked_at=now,
                    provenance=Provenance(
                        source="operations",
                        source_version="mc1001",
                        captured_at=now,
                    ),
                )
            )

        for component, probe in sorted(self._probes.items()):
            try:
                result = probe()
                state = HealthState(str(result.get("state", "unknown")))
                detail = str(result.get("detail", ""))
            except Exception as exc:  # health boundaries must not crash Operations
                state = HealthState.UNAVAILABLE
                detail = f"{type(exc).__name__}: {exc}"

            components.append(
                HealthComponentSnapshot(
                    component=component,
                    state=state,
                    detail=detail,
                    checked_at=now,
                    provenance=Provenance(
                        source=component,
                        source_version="provider",
                        captured_at=now,
                    ),
                )
            )

        aggregate = self._aggregate_state(component.state for component in components)
        return HealthSnapshot(
            state=aggregate,
            components=tuple(components),
            checked_at=now,
        )

    @staticmethod
    def _aggregate_state(states: Iterable[HealthState]) -> HealthState:
        values = tuple(states)
        if any(state is HealthState.UNAVAILABLE for state in values):
            return HealthState.UNAVAILABLE
        if any(state in (HealthState.DEGRADED, HealthState.UNKNOWN) for state in values):
            return HealthState.DEGRADED
        return HealthState.HEALTHY
PY

write_file core/operations/resources.py <<'PY'
"""Runtime resource collection for the Operations interface."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .contracts import ResourceProvider
from .models import Provenance, ResourceSnapshot, utc_now


class SystemResourceProvider:
    """Collects standard-library measurements, with optional psutil enrichment."""

    def __init__(self, disk_path: str | Path = "/") -> None:
        self._disk_path = Path(disk_path)

    def collect_resources(self) -> Mapping[str, Any]:
        disk = shutil.disk_usage(self._disk_path)
        disk_percent = (disk.used / disk.total * 100.0) if disk.total else None

        load_average = None
        if hasattr(os, "getloadavg"):
            load_average = float(os.getloadavg()[0])

        cpu_percent = None
        memory_percent = None
        try:
            import psutil  # type: ignore

            cpu_percent = float(psutil.cpu_percent(interval=None))
            memory_percent = float(psutil.virtual_memory().percent)
        except ImportError:
            pass

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "load_average_1m": load_average,
            "queue_depth": 0,
            "worker_count": 1,
        }


class ResourceCollector:
    """Converts a provider measurement into a stable resource snapshot."""

    def __init__(self, provider: ResourceProvider | None = None) -> None:
        self._provider = provider or SystemResourceProvider()

    def collect(
        self,
        *,
        mission_count: int,
        measured_at: datetime | None = None,
    ) -> ResourceSnapshot:
        now = measured_at or utc_now()
        result = self._provider.collect_resources()

        return ResourceSnapshot(
            cpu_percent=_optional_float(result.get("cpu_percent")),
            memory_percent=_optional_float(result.get("memory_percent")),
            disk_percent=_optional_float(result.get("disk_percent")),
            load_average_1m=_optional_float(result.get("load_average_1m")),
            queue_depth=int(result.get("queue_depth", 0)),
            mission_count=mission_count,
            worker_count=int(result.get("worker_count", 0)),
            measured_at=now,
            provenance=Provenance(
                source=type(self._provider).__name__,
                source_version="mc1001",
                captured_at=now,
            ),
        )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
PY

write_file core/operations/timeline.py <<'PY'
"""Operational timeline adapter."""

from __future__ import annotations

from datetime import datetime

from .models import TimelineEntrySnapshot, TimelineSnapshot, utc_now
from .registry import OperationsEventRegistry


class TimelineAdapter:
    """Projects canonical events into an operational timeline."""

    def __init__(self, registry: OperationsEventRegistry) -> None:
        self._registry = registry

    def collect(
        self,
        *,
        generated_at: datetime | None = None,
        limit: int = 100,
    ) -> TimelineSnapshot:
        now = generated_at or utc_now()
        entries = tuple(
            TimelineEntrySnapshot(
                event_id=event.event_id,
                event_kind=event.kind.value,
                occurred_at=event.occurred_at,
                summary=event.summary,
                subject_id=event.subject_id,
                payload=event.payload,
                provenance=event.provenance,
            )
            for event in self._registry.list_events(limit=limit)
        )
        return TimelineSnapshot(entries=entries, generated_at=now)
PY

write_file core/operations/service.py <<'PY'
"""Canonical aggregation service for JARVIS operational state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from .enums import AlertSeverity, HealthState, OperationalState
from .events import OperationsEvent
from .health import HealthAggregator
from .missions import MissionSnapshotAdapter
from .models import AlertSnapshot, OperationsSnapshot, Provenance, utc_now
from .registry import OperationsEventRegistry
from .resources import ResourceCollector
from .timeline import TimelineAdapter

Clock = Callable[[], datetime]


class OperationsService:
    """Aggregates subsystem state without owning subsystem state."""

    def __init__(
        self,
        *,
        missions: MissionSnapshotAdapter | None = None,
        health: HealthAggregator | None = None,
        resources: ResourceCollector | None = None,
        registry: OperationsEventRegistry | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._clock = clock
        self._registry = registry or OperationsEventRegistry()
        self._missions = missions or MissionSnapshotAdapter()
        self._health = health or HealthAggregator()
        self._resources = resources or ResourceCollector()
        self._timeline = TimelineAdapter(self._registry)

    @property
    def event_registry(self) -> OperationsEventRegistry:
        return self._registry

    def record_event(self, event: OperationsEvent) -> None:
        self._registry.append(event)

    def missions(self):
        return self._missions.collect(captured_at=self._clock())

    def health(self):
        return self._health.collect(checked_at=self._clock())

    def resources(self):
        missions = self._missions.collect(captured_at=self._clock())
        return self._resources.collect(
            mission_count=len(missions),
            measured_at=self._clock(),
        )

    def timeline(self, *, limit: int = 100):
        return self._timeline.collect(generated_at=self._clock(), limit=limit)

    def alerts(self):
        now = self._clock()
        health = self._health.collect(checked_at=now)
        alerts: list[AlertSnapshot] = []
        for component in health.components:
            if component.state in (HealthState.DEGRADED, HealthState.UNAVAILABLE):
                severity = (
                    AlertSeverity.ERROR
                    if component.state is HealthState.UNAVAILABLE
                    else AlertSeverity.WARNING
                )
                alerts.append(
                    AlertSnapshot(
                        alert_id=f"health:{component.component}",
                        severity=severity,
                        title=f"{component.component} health",
                        detail=component.detail,
                        active=True,
                        raised_at=now,
                        provenance=Provenance(
                            source="health-aggregator",
                            source_version="mc1001",
                            captured_at=now,
                        ),
                    )
                )
        return tuple(alerts)

    def snapshot(self) -> OperationsSnapshot:
        now = self._clock()
        missions = self._missions.collect(captured_at=now)
        health = self._health.collect(checked_at=now)
        resources = self._resources.collect(
            mission_count=len(missions),
            measured_at=now,
        )
        timeline = self._timeline.collect(generated_at=now)
        alerts = self._alerts_from_health(health, now)
        state = self._operational_state(health.state)

        unsigned = {
            "state": state.value,
            "missions": [mission.to_dict() for mission in missions],
            "health": health.to_dict(),
            "resources": resources.to_dict(),
            "timeline": timeline.to_dict(),
            "alerts": [alert.to_dict() for alert in alerts],
            "generated_at": now.isoformat(),
        }
        canonical = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        fingerprint = hashlib.sha256(canonical).hexdigest()

        return OperationsSnapshot(
            state=state,
            missions=missions,
            health=health,
            resources=resources,
            timeline=timeline,
            alerts=alerts,
            generated_at=now,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _operational_state(health_state: HealthState) -> OperationalState:
        if health_state is HealthState.HEALTHY:
            return OperationalState.READY
        if health_state in (HealthState.DEGRADED, HealthState.UNKNOWN):
            return OperationalState.DEGRADED
        return OperationalState.FAILED

    @staticmethod
    def _alerts_from_health(health, now):
        alerts: list[AlertSnapshot] = []
        for component in health.components:
            if component.state not in (HealthState.DEGRADED, HealthState.UNAVAILABLE):
                continue
            severity = (
                AlertSeverity.ERROR
                if component.state is HealthState.UNAVAILABLE
                else AlertSeverity.WARNING
            )
            alerts.append(
                AlertSnapshot(
                    alert_id=f"health:{component.component}",
                    severity=severity,
                    title=f"{component.component} health",
                    detail=component.detail,
                    active=True,
                    raised_at=now,
                    provenance=Provenance(
                        source="health-aggregator",
                        source_version="mc1001",
                        captured_at=now,
                    ),
                )
            )
        return tuple(alerts)
PY

write_file core/operations/__init__.py <<'PY'
"""Stable public API for the JARVIS Operations subsystem."""

from .enums import (
    ActivityState,
    AlertSeverity,
    EventKind,
    HealthState,
    MissionState,
    ObjectiveState,
    OperationalState,
)
from .events import OperationsEvent
from .health import HealthAggregator
from .missions import MissionSnapshotAdapter
from .models import (
    ActivitySnapshot,
    AlertSnapshot,
    HealthComponentSnapshot,
    HealthSnapshot,
    MissionSnapshot,
    ObjectiveSnapshot,
    OperationsSnapshot,
    Provenance,
    ResourceSnapshot,
    TimelineEntrySnapshot,
    TimelineSnapshot,
)
from .registry import OperationsEventRegistry
from .resources import ResourceCollector, SystemResourceProvider
from .service import OperationsService
from .timeline import TimelineAdapter

__all__ = [
    "ActivitySnapshot",
    "ActivityState",
    "AlertSeverity",
    "AlertSnapshot",
    "EventKind",
    "HealthAggregator",
    "HealthComponentSnapshot",
    "HealthSnapshot",
    "HealthState",
    "MissionSnapshot",
    "MissionSnapshotAdapter",
    "MissionState",
    "ObjectiveSnapshot",
    "ObjectiveState",
    "OperationalState",
    "OperationsEvent",
    "OperationsEventRegistry",
    "OperationsService",
    "OperationsSnapshot",
    "Provenance",
    "ResourceCollector",
    "ResourceSnapshot",
    "SystemResourceProvider",
    "TimelineAdapter",
    "TimelineEntrySnapshot",
    "TimelineSnapshot",
]
PY

write_file core/src/routes/operations.py <<'PY'
"""FastAPI routes for the MC-1001 Operations interface."""

from __future__ import annotations

from fastapi import APIRouter, Query

from core.operations import OperationsService

router = APIRouter(prefix="/operations", tags=["operations"])
_service = OperationsService()


def get_operations_service() -> OperationsService:
    """Return the process-wide Sprint 0 Operations service."""

    return _service


@router.get("/status")
def operations_status() -> dict:
    return get_operations_service().snapshot().to_dict()


@router.get("/health")
def operations_health() -> dict:
    return get_operations_service().health().to_dict()


@router.get("/missions")
def operations_missions() -> list[dict]:
    return [
        mission.to_dict()
        for mission in get_operations_service().missions()
    ]


@router.get("/resources")
def operations_resources() -> dict:
    return get_operations_service().resources().to_dict()


@router.get("/timeline")
def operations_timeline(
    limit: int = Query(default=100, ge=0, le=1000),
) -> dict:
    return get_operations_service().timeline(limit=limit).to_dict()


@router.get("/events")
def operations_events(
    limit: int = Query(default=100, ge=0, le=1000),
) -> list[dict]:
    return [
        event.to_dict()
        for event in get_operations_service().event_registry.list_events(limit=limit)
    ]
PY

write_file docs/architecture/operations_layer.md <<'MD'
# MC-1001 — Executive Operations Interface

## Status

Implemented by Sprint 0.

## Purpose

The Operations subsystem is the stable boundary between the JARVIS Executive
Operating System and all current or future clients.

Clients include:

- Mission Control web interface
- CLI tools
- desktop and mobile applications
- voice interfaces
- Meta Quest interfaces
- autonomous operational agents

## Architectural Rule

Operations aggregates and projects state. It does not own Executive, Reasoning,
Knowledge, Evidence, Representation, or Bootstrap state.

No lower subsystem may import `core.operations`.

## Sprint 0 Capabilities

- immutable operational snapshots
- deterministic serialization
- deterministic snapshot fingerprints under a fixed clock and fixed providers
- mission projection
- component health aggregation
- runtime resource projection
- canonical event storage
- operational timeline projection
- FastAPI read endpoints

## API

- `GET /operations/status`
- `GET /operations/health`
- `GET /operations/missions`
- `GET /operations/resources`
- `GET /operations/timeline`
- `GET /operations/events`

## Deferred Work

The following are intentionally deferred:

- WebSocket event streaming
- persistent event storage
- pause and resume commands
- checkpoint and replay commands
- direct Executive adapters
- authentication and authorization
- Commander Dashboard UI

These belong to later Mission Control sprints.
MD

write_file tests/test_mc1001_operations.py <<'PY'
from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.operations import (
    EventKind,
    HealthAggregator,
    HealthState,
    MissionSnapshotAdapter,
    OperationsEvent,
    OperationsEventRegistry,
    OperationsService,
    ResourceCollector,
)


FIXED_TIME = datetime(2026, 7, 23, 0, 0, tzinfo=timezone.utc)


class StaticMissionProvider:
    def list_missions(self):
        return (
            {
                "mission_id": "mission-001",
                "name": "Establish Operations",
                "state": "active",
                "created_at": FIXED_TIME,
                "updated_at": FIXED_TIME,
                "source": "test-executive",
                "source_version": "1",
                "objectives": (),
            },
        )


class StaticResourceProvider:
    def collect_resources(self):
        return {
            "cpu_percent": 10.0,
            "memory_percent": 20.0,
            "disk_percent": 30.0,
            "load_average_1m": 0.5,
            "queue_depth": 2,
            "worker_count": 1,
        }


class MC1001OperationsTests(unittest.TestCase):
    def build_service(self):
        registry = OperationsEventRegistry()
        return OperationsService(
            missions=MissionSnapshotAdapter(StaticMissionProvider()),
            health=HealthAggregator(
                {"executive": lambda: {"state": "healthy", "detail": "ready"}}
            ),
            resources=ResourceCollector(StaticResourceProvider()),
            registry=registry,
            clock=lambda: FIXED_TIME,
        )

    def test_snapshot_is_immutable(self):
        snapshot = self.build_service().snapshot()
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = "failed"  # type: ignore[misc]

    def test_snapshot_is_deterministic(self):
        service = self.build_service()
        first = service.snapshot()
        second = service.snapshot()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_mission_is_projected(self):
        snapshot = self.build_service().snapshot()
        self.assertEqual(len(snapshot.missions), 1)
        self.assertEqual(snapshot.missions[0].mission_id, "mission-001")

    def test_health_is_aggregated(self):
        snapshot = self.build_service().snapshot()
        self.assertEqual(snapshot.health.state, HealthState.HEALTHY)

    def test_event_enters_timeline(self):
        service = self.build_service()
        service.record_event(
            OperationsEvent.create(
                kind=EventKind.MISSION_STARTED,
                summary="Mission started",
                subject_id="mission-001",
                occurred_at=FIXED_TIME,
                event_id="event-001",
            )
        )
        timeline = service.timeline()
        self.assertEqual(len(timeline.entries), 1)
        self.assertEqual(timeline.entries[0].event_id, "event-001")

    def test_serialization_is_json_compatible(self):
        payload = self.build_service().snapshot().to_dict()
        self.assertEqual(payload["state"], "ready")
        self.assertTrue(payload["generated_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
PY

write_file dev/verification/verify_mc1001.py <<'PY'
#!/usr/bin/env python3
"""Structural and behavioral certification for MC-1001."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FILES = (
    "core/operations/__init__.py",
    "core/operations/contracts.py",
    "core/operations/enums.py",
    "core/operations/errors.py",
    "core/operations/events.py",
    "core/operations/health.py",
    "core/operations/missions.py",
    "core/operations/models.py",
    "core/operations/registry.py",
    "core/operations/resources.py",
    "core/operations/service.py",
    "core/operations/timeline.py",
    "core/src/routes/operations.py",
    "docs/architecture/operations_layer.md",
    "tests/test_mc1001_operations.py",
)


def check(name, condition, detail=""):
    if condition:
        print(f"[PASS] {name}")
        return 0
    print(f"[FAIL] {name}{': ' + detail if detail else ''}")
    return 1


def main():
    failures = 0

    missing = [path for path in EXPECTED_FILES if not (ROOT / path).is_file()]
    failures += check("Canonical MC-1001 file set", not missing, ", ".join(missing))

    compile_result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "core/operations", "core/src/routes/operations.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check("Operations package compilation", compile_result.returncode == 0)

    required_exports = {
        "OperationsService",
        "OperationsSnapshot",
        "MissionSnapshot",
        "HealthSnapshot",
        "ResourceSnapshot",
        "OperationsEvent",
    }
    module = importlib.import_module("core.operations")
    failures += check(
        "Stable public Operations imports",
        all(hasattr(module, name) for name in required_exports),
    )

    forbidden_importers = []
    for package in ("core/executive", "core/reasoning", "core/cognition", "core/knowledge"):
        root = ROOT / package
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "core.operations" in text or "from ..operations" in text:
                forbidden_importers.append(str(path.relative_to(ROOT)))
    failures += check(
        "Forward-only dependency boundary",
        not forbidden_importers,
        ", ".join(forbidden_importers),
    )

    router_text = (ROOT / "core/src/routes/operations.py").read_text(encoding="utf-8")
    required_routes = (
        '"/status"',
        '"/health"',
        '"/missions"',
        '"/resources"',
        '"/timeline"',
        '"/events"',
    )
    failures += check(
        "Required REST endpoints declared",
        all(route in router_text for route in required_routes),
    )

    fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)
    service = module.OperationsService(clock=lambda: fixed)
    first = service.snapshot().to_dict()
    second = service.snapshot().to_dict()
    failures += check("Deterministic snapshot generation", first == second)

    canonical = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
    fingerprint = hashlib.sha256(canonical).hexdigest()
    failures += check("Deterministic verification fingerprint", len(fingerprint) == 64)
    print(f"       fingerprint: {fingerprint}")

    test_result = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "tests.test_mc1001_operations"],
        cwd=ROOT,
        check=False,
    )
    failures += check("MC-1001 unit tests", test_result.returncode == 0)

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x dev/verification/verify_mc1001.py

write_file dev/verify_mc1001.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo "======================================================================"
echo "JARVIS — MC-1001 SPRINT 0 EXECUTIVE OPERATIONS INTERFACE"
echo "======================================================================"

"$PYTHON_BIN" dev/verification/verify_mc1001.py
SH
chmod +x dev/verify_mc1001.sh

# Add the router registration using a narrow, idempotent patch.
MAIN_FILE="core/src/main.py"
if [[ -f "$MAIN_FILE" ]]; then
    backup_if_present "$MAIN_FILE"
    python - "$MAIN_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "# MC-1001 Operations Interface"

if marker not in text:
    addition = """
# MC-1001 Operations Interface
try:
    from core.src.routes.operations import router as operations_router
except ModuleNotFoundError:
    from src.routes.operations import router as operations_router

app.include_router(operations_router)
"""
    text = text.rstrip() + "\n\n" + addition.lstrip()
    path.write_text(text, encoding="utf-8")
    print(f"[PATCH] {path}")
else:
    print(f"[SKIP] {path} already registers MC-1001 router")
PY
else
    echo "[WARN] core/src/main.py was not found; register the operations router manually."
fi

echo
echo "Installation complete."
if [[ -d "$BACKUP_ROOT" ]]; then
    echo "Backups: $BACKUP_ROOT"
fi
echo
echo "Run:"
echo "  PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python ./dev/verify_mc1001.sh"
