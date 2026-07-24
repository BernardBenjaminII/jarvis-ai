#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS — GENESIS VI-A1 EXECUTIVE TELEMETRY FOUNDATION"
echo "======================================================================"

required_files=(
    "core/operations/service.py"
    "core/operations/models.py"
    "core/operations/contracts.py"
    "core/operations/enums.py"
    "core/src/static/mission_control/app.js"
    "tests/test_mc1001_operations.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "[FAIL] Required prerequisite missing: $file"
        exit 1
    fi
done

if grep -q "executive_status" core/src/main.py; then
    echo "[FAIL] core/src/main.py still references the abandoned executive_status router."
    echo "       Remove its import and app.include_router(...) line before continuing."
    exit 1
fi

mkdir -p \
    core/operations \
    core/src/static/mission_control \
    tests \
    dev/verification \
    docs/architecture

cat > core/operations/enums.py <<'EOF'
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


class ExecutiveState(str, Enum):
    """Externally visible state of the Executive runtime."""

    INITIALIZING = "initializing"
    READY = "ready"
    OBSERVING = "observing"
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    PAUSED = "paused"
    DEGRADED = "degraded"
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
EOF

cat > core/operations/contracts.py <<'EOF'
"""Provider contracts consumed by the Operations service."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ExecutiveProvider(Protocol):
    """Projects Executive runtime state without exposing Executive internals."""

    def collect_executive_state(self) -> Mapping[str, Any]:
        """Return one Executive telemetry record."""


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
EOF

cat > core/operations/models.py <<'EOF'
"""Immutable snapshot models for the JARVIS Operations interface."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from .enums import (
    ActivityState,
    AlertSeverity,
    ExecutiveState,
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
class ExecutiveSnapshot(SerializableSnapshot):
    """Immutable projection of the Executive runtime."""

    state: ExecutiveState
    mode: str
    heartbeat_at: datetime
    started_at: datetime | None
    uptime_seconds: float
    current_activity: str | None
    active_mission_id: str | None
    active_objective_id: str | None
    active_activity_id: str | None
    observation_count: int
    pending_observations: int
    decision_queue_depth: int
    reasoning_queue_depth: int
    pending_authorizations: int
    confidence: float | None
    last_cycle_at: datetime | None
    last_cycle_duration_ms: float | None
    provenance: Provenance


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
    executive: ExecutiveSnapshot
    missions: tuple[MissionSnapshot, ...]
    health: HealthSnapshot
    resources: ResourceSnapshot
    timeline: TimelineSnapshot
    alerts: tuple[AlertSnapshot, ...]
    generated_at: datetime
    fingerprint: str
EOF

cat > core/operations/executive.py <<'EOF'
"""Executive telemetry projection for the Operations subsystem."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .contracts import ExecutiveProvider
from .enums import ExecutiveState
from .models import ExecutiveSnapshot, Provenance, utc_now


class SystemExecutiveProvider:
    """Provides safe baseline telemetry until live Executive bindings exist."""

    def __init__(self, *, started_at: datetime | None = None) -> None:
        self._started_at = _as_utc(started_at or utc_now())

    def collect_executive_state(self) -> Mapping[str, Any]:
        return {
            "state": ExecutiveState.READY.value,
            "mode": "command",
            "started_at": self._started_at,
            "current_activity": "Awaiting commander direction.",
            "observation_count": 0,
            "pending_observations": 0,
            "decision_queue_depth": 0,
            "reasoning_queue_depth": 0,
            "pending_authorizations": 0,
            "source": "executive-runtime",
            "source_version": "genesis-vi-a1",
        }


class ExecutiveTelemetryAdapter:
    """Converts Executive provider output into a stable snapshot."""

    def __init__(self, provider: ExecutiveProvider | None = None) -> None:
        self._provider = provider or SystemExecutiveProvider()

    def collect(
        self,
        *,
        captured_at: datetime | None = None,
    ) -> ExecutiveSnapshot:
        now = _as_utc(captured_at or utc_now())

        try:
            record = dict(self._provider.collect_executive_state())
        except Exception as exc:
            record = {
                "state": ExecutiveState.FAILED.value,
                "mode": "recovery",
                "current_activity": (
                    f"Executive telemetry unavailable: {type(exc).__name__}: {exc}"
                ),
                "source": type(self._provider).__name__,
                "source_version": "provider-error",
            }

        state = _executive_state(record.get("state"))
        started_at = _optional_datetime(record.get("started_at"))
        heartbeat_at = _optional_datetime(record.get("heartbeat_at")) or now

        supplied_uptime = record.get("uptime_seconds")
        if supplied_uptime is not None:
            uptime_seconds = _nonnegative_float(supplied_uptime)
        elif started_at is not None:
            uptime_seconds = max(0.0, (now - started_at).total_seconds())
        else:
            uptime_seconds = 0.0

        return ExecutiveSnapshot(
            state=state,
            mode=str(record.get("mode", "unknown")),
            heartbeat_at=heartbeat_at,
            started_at=started_at,
            uptime_seconds=uptime_seconds,
            current_activity=_optional_text(record.get("current_activity")),
            active_mission_id=_optional_text(record.get("active_mission_id")),
            active_objective_id=_optional_text(record.get("active_objective_id")),
            active_activity_id=_optional_text(record.get("active_activity_id")),
            observation_count=_nonnegative_int(record.get("observation_count", 0)),
            pending_observations=_nonnegative_int(
                record.get("pending_observations", 0)
            ),
            decision_queue_depth=_nonnegative_int(
                record.get("decision_queue_depth", 0)
            ),
            reasoning_queue_depth=_nonnegative_int(
                record.get("reasoning_queue_depth", 0)
            ),
            pending_authorizations=_nonnegative_int(
                record.get("pending_authorizations", 0)
            ),
            confidence=_optional_confidence(record.get("confidence")),
            last_cycle_at=_optional_datetime(record.get("last_cycle_at")),
            last_cycle_duration_ms=_optional_nonnegative_float(
                record.get("last_cycle_duration_ms")
            ),
            provenance=Provenance(
                source=str(
                    record.get("source", type(self._provider).__name__)
                ),
                source_version=str(
                    record.get("source_version", "provider")
                ),
                captured_at=now,
            ),
        )


def _executive_state(value: Any) -> ExecutiveState:
    try:
        return ExecutiveState(str(value or ExecutiveState.INITIALIZING.value))
    except ValueError:
        return ExecutiveState.DEGRADED


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _nonnegative_int(value: Any) -> int:
    return max(0, int(value))


def _nonnegative_float(value: Any) -> float:
    return max(0.0, float(value))


def _optional_nonnegative_float(value: Any) -> float | None:
    return None if value is None else _nonnegative_float(value)


def _optional_confidence(value: Any) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _as_utc(value)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        return _as_utc(datetime.fromisoformat(normalized))
    raise TypeError(f"unsupported datetime value: {type(value).__name__}")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
EOF

cat > core/operations/service.py <<'EOF'
"""Canonical aggregation service for JARVIS operational state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from .enums import AlertSeverity, HealthState, OperationalState
from .events import OperationsEvent
from .executive import ExecutiveTelemetryAdapter
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
        executive: ExecutiveTelemetryAdapter | None = None,
        missions: MissionSnapshotAdapter | None = None,
        health: HealthAggregator | None = None,
        resources: ResourceCollector | None = None,
        registry: OperationsEventRegistry | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._clock = clock
        self._registry = registry or OperationsEventRegistry()
        self._executive = executive or ExecutiveTelemetryAdapter()
        self._missions = missions or MissionSnapshotAdapter()
        self._health = health or HealthAggregator()
        self._resources = resources or ResourceCollector()
        self._timeline = TimelineAdapter(self._registry)

    @property
    def event_registry(self) -> OperationsEventRegistry:
        return self._registry

    def record_event(self, event: OperationsEvent) -> None:
        self._registry.append(event)

    def executive(self):
        return self._executive.collect(captured_at=self._clock())

    def missions(self):
        return self._missions.collect(captured_at=self._clock())

    def health(self):
        return self._health.collect(checked_at=self._clock())

    def resources(self):
        now = self._clock()
        missions = self._missions.collect(captured_at=now)
        return self._resources.collect(
            mission_count=len(missions),
            measured_at=now,
        )

    def timeline(self, *, limit: int = 100):
        return self._timeline.collect(generated_at=self._clock(), limit=limit)

    def alerts(self):
        now = self._clock()
        health = self._health.collect(checked_at=now)
        return self._alerts_from_health(health, now)

    def snapshot(self) -> OperationsSnapshot:
        now = self._clock()
        executive = self._executive.collect(captured_at=now)
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
            "executive": executive.to_dict(),
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
            executive=executive,
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
            if component.state not in (
                HealthState.DEGRADED,
                HealthState.UNAVAILABLE,
            ):
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
EOF

cat > core/operations/__init__.py <<'EOF'
"""Stable public API for the JARVIS Operations subsystem."""

from .enums import (
    ActivityState,
    AlertSeverity,
    EventKind,
    ExecutiveState,
    HealthState,
    MissionState,
    ObjectiveState,
    OperationalState,
)
from .events import OperationsEvent
from .executive import ExecutiveTelemetryAdapter, SystemExecutiveProvider
from .health import HealthAggregator
from .missions import MissionSnapshotAdapter
from .models import (
    ActivitySnapshot,
    AlertSnapshot,
    ExecutiveSnapshot,
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
    "ExecutiveSnapshot",
    "ExecutiveState",
    "ExecutiveTelemetryAdapter",
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
    "SystemExecutiveProvider",
    "SystemResourceProvider",
    "TimelineAdapter",
    "TimelineEntrySnapshot",
    "TimelineSnapshot",
]
EOF

cat > core/src/static/mission_control/app.js <<'EOF'
"use strict";

const E = {
  status: "/operations/status",
  health: "/operations/health",
  missions: "/operations/missions",
  resources: "/operations/resources",
  timeline: "/operations/timeline",
  events: "/operations/events"
};

const $ = id => document.getElementById(id);
const pick = (...values) =>
  values.find(value => value !== undefined && value !== null);
const list = value =>
  Array.isArray(value)
    ? value
    : Array.isArray(value?.items)
      ? value.items
      : Array.isArray(value?.results)
        ? value.results
        : [];
const norm = value =>
  String(value || "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-");
const esc = value =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const stamp = value => {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value || "UNKNOWN")
    : date.toLocaleString();
};

function pill(element, value) {
  element.className = `pill ${norm(value)}`;
  element.textContent = String(value || "UNKNOWN").toUpperCase();
}

async function get(url) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" }
  });

  if (!response.ok) {
    throw Error(`${url}: ${response.status}`);
  }

  return response.json();
}

function connection(ok) {
  $("link").textContent = ok ? "OPERATIONS LINK" : "LINK DEGRADED";
  $("link").className = `pill ${ok ? "connected" : "disconnected"}`;
  $("api").textContent = ok ? "CONNECTED" : "DEGRADED";
}

function readinessFor(state, confidence) {
  if (typeof confidence === "number") {
    return Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  }

  const values = {
    ready: 100,
    observing: 92,
    reasoning: 88,
    planning: 88,
    executing: 90,
    waiting: 85,
    initializing: 35,
    paused: 50,
    degraded: 60,
    failed: 0,
    stopped: 0
  };

  return values[norm(state)] ?? 0;
}

function status(payload) {
  const executive = payload?.executive || {};
  const state = pick(
    executive.state,
    payload.state,
    payload.status,
    payload.operational_state,
    "unknown"
  );
  const confidence = pick(executive.confidence, payload.readiness);
  const readiness = readinessFor(state, confidence);
  const heartbeat = pick(
    executive.heartbeat_at,
    payload.generated_at,
    payload.timestamp
  );

  $("status").textContent = String(state).toUpperCase();
  $("status").className = norm(state);
  $("status-detail").textContent = pick(
    executive.current_activity,
    payload.detail,
    payload.message,
    payload.summary,
    `Executive mode: ${executive.mode || "unknown"}.`
  );
  $("readiness").textContent = `${readiness}%`;
  $("snapshot-time").textContent = heartbeat
    ? `Heartbeat ${stamp(heartbeat)}`
    : "Executive telemetry received";
}

function missions(payload) {
  const all = list(payload);
  const mission =
    all.find(item =>
      ["active", "running", "executing", "in-progress"].includes(
        norm(pick(item.state, item.status))
      )
    ) || all[0];

  const counts = { active: 0, queued: 0, complete: 0 };

  all.forEach(item => {
    const state = norm(pick(item.state, item.status));
    if (["active", "running", "executing", "in-progress"].includes(state)) {
      counts.active++;
    } else if (
      ["complete", "completed", "certified", "done"].includes(state)
    ) {
      counts.complete++;
    } else {
      counts.queued++;
    }
  });

  $("active").textContent = pick(payload.active_count, counts.active);
  $("queued").textContent = pick(payload.queued_count, counts.queued);
  $("complete").textContent = pick(
    payload.completed_count,
    payload.complete_count,
    counts.complete
  );

  if (!mission) {
    pill($("mission-state"), "idle");
    return;
  }

  $("mission").textContent = pick(
    mission.title,
    mission.name,
    mission.mission_id,
    "Active mission"
  );
  $("objective").textContent = pick(
    mission.objective,
    mission.description,
    mission.summary,
    "Mission objective not supplied."
  );
  pill($("mission-state"), pick(mission.state, mission.status, "active"));
}

function health(payload) {
  let components = list(payload);

  if (!components.length && payload && typeof payload === "object") {
    components = Object.entries(payload)
      .filter(([, value]) => value && typeof value === "object")
      .map(([name, value]) => ({ name, ...value }));
  }

  $("divisions-list").innerHTML = [
    "operations",
    "knowledge",
    "reasoning",
    "cognition"
  ].map(name => {
    const component = components.find(
      item => norm(pick(item.name, item.component, item.service)) === name
    );
    const state = pick(
      component?.state,
      component?.status,
      component?.health,
      "unknown"
    );

    return `
      <div class="row">
        <span>${name[0].toUpperCase() + name.slice(1)}</span>
        <span class="pill ${norm(state)}">${esc(
          String(state).toUpperCase()
        )}</span>
      </div>`;
  }).join("");
}

function resources(payload) {
  const items = list(payload);
  const find = name =>
    items.find(
      item => norm(pick(item.name, item.kind, item.resource)) === name
    );

  $("resources-list").innerHTML = ["cpu", "memory", "storage"].map(name => {
    let value = pick(
      payload?.[name],
      payload?.[`${name}_percent`],
      name === "storage" ? payload?.disk_percent : null,
      find(name)
    );

    if (value && typeof value === "object") {
      value = pick(
        value.percent,
        value.utilization,
        value.used_percent,
        value.value
      );
    }

    const percent =
      typeof value === "number"
        ? Math.max(0, Math.min(100, value <= 1 ? value * 100 : value))
        : 0;

    return `
      <div class="resource">
        <div class="resource-title">
          <span>${name.toUpperCase()}</span>
          <b>${percent ? `${Math.round(percent)}%` : "--"}</b>
        </div>
        <div class="meter"><i style="width:${percent}%"></i></div>
      </div>`;
  }).join("");
}

function timeline(payload) {
  const entries = list(payload).slice(0, 12);
  $("event-count").textContent = `${entries.length} EVENTS`;
  $("timeline").innerHTML = entries.length
    ? entries.map(entry => `
        <li class="event">
          <time>${esc(
            stamp(
              pick(
                entry.timestamp,
                entry.occurred_at,
                entry.created_at
              )
            )
          )}</time>
          <div>
            <b>${esc(
              pick(
                entry.title,
                entry.name,
                entry.event_type,
                entry.event_kind,
                entry.type,
                "Operational event"
              )
            )}</b>
            <p>${esc(
              pick(
                entry.detail,
                entry.description,
                entry.message,
                entry.summary,
                ""
              )
            )}</p>
          </div>
        </li>`).join("")
    : '<li class="empty">No operational events received.</li>';
}

function cards(payload, key, target, count, label) {
  const entries = list(payload?.[key]);
  $(count).textContent = `${entries.length} ${label}`;
  $(target).innerHTML = entries.length
    ? entries.slice(0, 5).map(entry => `
        <div class="card">
          <b>${esc(
            pick(
              entry.title,
              entry.name,
              key === "alerts" ? entry.severity : "Recommendation"
            )
          )}</b>
          <p>${esc(
            pick(
              entry.rationale,
              entry.detail,
              entry.description,
              entry.message,
              entry.summary,
              ""
            )
          )}</p>
        </div>`).join("")
    : `No ${
        key === "alerts"
          ? "active operational alerts"
          : "recommendations require authorization"
      }.`;
}

async function refresh() {
  const button = $("refresh");
  button.disabled = true;
  button.textContent = "Refreshing Operational Picture";

  const pairs = await Promise.all(
    Object.entries(E).map(async ([key, url]) => {
      try {
        return [key, await get(url), null];
      } catch (error) {
        return [key, null, error];
      }
    })
  );

  const results = Object.fromEntries(
    pairs.map(([key, data, error]) => [key, { data, error }])
  );

  connection(Object.values(results).some(result => !result.error));

  if (results.status.data) {
    status(results.status.data);
  }
  if (results.missions.data) {
    missions(results.missions.data);
  }
  if (results.health.data) {
    health(results.health.data);
  }
  if (results.resources.data) {
    resources(results.resources.data);
  }

  timeline(results.timeline.data || results.events.data || {});

  cards(
    results.status.data || {},
    "recommendations",
    "recommendations",
    "recommendation-count",
    "PENDING"
  );
  cards(
    results.status.data || {},
    "alerts",
    "alerts",
    "alert-count",
    "ACTIVE"
  );

  $("sync").textContent = new Date().toLocaleTimeString();
  button.disabled = false;
  button.textContent = "Refresh Operational Picture";
}

document.addEventListener("DOMContentLoaded", () => {
  setInterval(() => {
    $("clock").textContent = new Date().toLocaleTimeString([], {
      hour12: false
    });
  }, 1000);

  $("refresh").addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 15000);
});
EOF

cat > tests/test_mc1001_operations.py <<'EOF'
from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.operations import (
    EventKind,
    ExecutiveState,
    ExecutiveTelemetryAdapter,
    HealthAggregator,
    HealthState,
    MissionSnapshotAdapter,
    OperationsEvent,
    OperationsEventRegistry,
    OperationsService,
    ResourceCollector,
)


FIXED_TIME = datetime(2026, 7, 23, 0, 0, tzinfo=timezone.utc)


class StaticExecutiveProvider:
    def collect_executive_state(self):
        return {
            "state": "reasoning",
            "mode": "command",
            "heartbeat_at": FIXED_TIME,
            "started_at": FIXED_TIME,
            "uptime_seconds": 120.0,
            "current_activity": "Evaluating verified evidence.",
            "active_mission_id": "mission-001",
            "observation_count": 12,
            "pending_observations": 3,
            "decision_queue_depth": 2,
            "reasoning_queue_depth": 1,
            "pending_authorizations": 1,
            "confidence": 0.875,
            "last_cycle_at": FIXED_TIME,
            "last_cycle_duration_ms": 18.5,
            "source": "test-executive",
            "source_version": "1",
        }


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
            executive=ExecutiveTelemetryAdapter(StaticExecutiveProvider()),
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

    def test_executive_is_projected(self):
        snapshot = self.build_service().snapshot()
        self.assertEqual(snapshot.executive.state, ExecutiveState.REASONING)
        self.assertEqual(snapshot.executive.active_mission_id, "mission-001")
        self.assertEqual(snapshot.executive.confidence, 0.875)

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
        self.assertEqual(payload["executive"]["state"], "reasoning")
        self.assertTrue(payload["generated_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_genesis_vi_a1_executive_telemetry.py <<'EOF'
from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from core.operations import (
    ExecutiveState,
    ExecutiveTelemetryAdapter,
    OperationsService,
)


CAPTURED_AT = datetime(2026, 7, 23, 1, 0, tzinfo=timezone.utc)
STARTED_AT = CAPTURED_AT - timedelta(minutes=5)


class CompleteProvider:
    def collect_executive_state(self):
        return {
            "state": "executing",
            "mode": "command",
            "started_at": STARTED_AT,
            "current_activity": "Executing certified plan.",
            "active_mission_id": "mission-vi-a1",
            "active_objective_id": "objective-telemetry",
            "active_activity_id": "activity-project",
            "observation_count": 40,
            "pending_observations": 4,
            "decision_queue_depth": 2,
            "reasoning_queue_depth": 3,
            "pending_authorizations": 1,
            "confidence": 0.91,
            "last_cycle_at": CAPTURED_AT,
            "last_cycle_duration_ms": 12.75,
            "source": "certification-provider",
            "source_version": "vi-a1",
        }


class InvalidStateProvider:
    def collect_executive_state(self):
        return {
            "state": "impossible-state",
            "confidence": 4.0,
            "observation_count": -10,
        }


class FailingProvider:
    def collect_executive_state(self):
        raise RuntimeError("telemetry source offline")


class GenesisVIA1Tests(unittest.TestCase):
    def test_complete_provider_projection(self):
        snapshot = ExecutiveTelemetryAdapter(CompleteProvider()).collect(
            captured_at=CAPTURED_AT
        )
        self.assertEqual(snapshot.state, ExecutiveState.EXECUTING)
        self.assertEqual(snapshot.uptime_seconds, 300.0)
        self.assertEqual(snapshot.active_mission_id, "mission-vi-a1")
        self.assertEqual(snapshot.pending_authorizations, 1)

    def test_snapshot_is_immutable(self):
        snapshot = ExecutiveTelemetryAdapter(CompleteProvider()).collect(
            captured_at=CAPTURED_AT
        )
        with self.assertRaises(FrozenInstanceError):
            snapshot.mode = "autonomous"  # type: ignore[misc]

    def test_invalid_values_are_safely_bounded(self):
        snapshot = ExecutiveTelemetryAdapter(InvalidStateProvider()).collect(
            captured_at=CAPTURED_AT
        )
        self.assertEqual(snapshot.state, ExecutiveState.DEGRADED)
        self.assertEqual(snapshot.confidence, 1.0)
        self.assertEqual(snapshot.observation_count, 0)

    def test_provider_failure_becomes_failed_telemetry(self):
        snapshot = ExecutiveTelemetryAdapter(FailingProvider()).collect(
            captured_at=CAPTURED_AT
        )
        self.assertEqual(snapshot.state, ExecutiveState.FAILED)
        self.assertIn("RuntimeError", snapshot.current_activity or "")

    def test_default_service_exposes_executive_snapshot(self):
        service = OperationsService(clock=lambda: CAPTURED_AT)
        payload = service.snapshot().to_dict()
        self.assertIn("executive", payload)
        self.assertIn("heartbeat_at", payload["executive"])
        self.assertIn("current_activity", payload["executive"])

    def test_executive_changes_fingerprint_contract(self):
        service = OperationsService(
            executive=ExecutiveTelemetryAdapter(CompleteProvider()),
            clock=lambda: CAPTURED_AT,
        )
        snapshot = service.snapshot()
        self.assertEqual(len(snapshot.fingerprint), 64)
        self.assertEqual(
            snapshot.to_dict()["executive"]["source"]
            if "source" in snapshot.to_dict()["executive"]
            else snapshot.to_dict()["executive"]["provenance"]["source"],
            "certification-provider",
        )


if __name__ == "__main__":
    unittest.main()
EOF

cat > docs/architecture/executive_telemetry_architecture.md <<'EOF'
# Genesis VI-A1 — Executive Telemetry Architecture

**Status:** Implemented  
**Architecture version:** Executive Architecture 1.0  
**Milestone:** Genesis VI-A1  
**Subsystem:** Operations

## Purpose

Executive telemetry is the stable, immutable projection through which JARVIS
reports its current Executive state.

It does not own missions, reasoning, observations, planning, authority, or
execution. It projects those subsystem states into a deterministic operational
contract suitable for APIs, Mission Control, auditing, and future interfaces.

## Canonical flow

```text
Executive runtime and subsystem providers
                    |
                    v
        ExecutiveTelemetryAdapter
                    |
                    v
            ExecutiveSnapshot
                    |
                    v
            OperationsSnapshot
                    |
                    v
          /operations/status
                    |
                    v
           Commander's Bridge
Architectural rules
Operations remains the single public aggregation boundary.
Executive telemetry does not introduce a parallel Executive-status API.
Providers expose mappings and do not leak internal mutable objects.
Snapshots are immutable and JSON-compatible.
Snapshot generation is deterministic for identical provider state and time.
Executive telemetry participates in the Operations fingerprint.
Provider failures degrade telemetry without crashing Operations.
Future fields must be added compatibly rather than silently renamed.
ExecutiveSnapshot domains
Runtime identity
state
mode
heartbeat
process start
uptime
current activity
Mission context
active mission
active objective
active activity
Cognition and reasoning
total observations
pending observations
reasoning queue depth
confidence
last cognitive cycle
Planning and authority
decision queue depth
pending authorizations
Provenance

Every Executive snapshot identifies:

provider source
provider version
capture time
Current provider

Genesis VI-A1 includes SystemExecutiveProvider, a safe baseline provider that
reports the Executive as ready and awaiting commander direction.

Later phases will replace or enrich this provider with adapters to the live
Executive, observation, reasoning, planning, mission, and authority subsystems.
The public snapshot contract does not need to change when those bindings are
introduced.

Compatibility boundary

Mission Control reads Executive state exclusively through
/operations/status.

No browser code may call Executive, reasoning, knowledge, cognition, or
planning internals directly.
EOF

cat > dev/verification/verify_genesis_vi_a1.py <<'EOF'
#!/usr/bin/env python3
"""Structural certification for Genesis VI-A1."""

from future import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(file).resolve().parents[2]

REQUIRED_FILES = (
"core/operations/executive.py",
"core/operations/models.py",
"core/operations/service.py",
"core/operations/init.py",
"core/src/static/mission_control/app.js",
"tests/test_genesis_vi_a1_executive_telemetry.py",
"docs/architecture/executive_telemetry_architecture.md",
)

checks_failed = 0

def check(condition: bool, description: str) -> None:
global checks_failed
if condition:
print(f"[PASS] {description}")
else:
checks_failed += 1
print(f"[FAIL] {description}")

def read(relative: str) -> str:
return (ROOT / relative).read_text(encoding="utf-8")

def main() -> int:
print()
print("=" * 70)
print("JARVIS — GENESIS VI-A1 EXECUTIVE TELEMETRY CERTIFICATION")
print("=" * 70)

check(
    all((ROOT / path).is_file() for path in REQUIRED_FILES),
    "Required Genesis VI-A1 artifacts",
)

parse_targets = (
    "core/operations/enums.py",
    "core/operations/contracts.py",
    "core/operations/models.py",
    "core/operations/executive.py",
    "core/operations/service.py",
    "core/operations/__init__.py",
    "tests/test_genesis_vi_a1_executive_telemetry.py",
)

parse_ok = True
for path in parse_targets:
    try:
        ast.parse(read(path), filename=path)
    except SyntaxError:
        parse_ok = False
check(parse_ok, "Python structural parse")

models = read("core/operations/models.py")
service = read("core/operations/service.py")
public_api = read("core/operations/__init__.py")
bridge = read("core/src/static/mission_control/app.js")
main_source = read("core/src/main.py")

check(
    "class ExecutiveSnapshot" in models
    and "executive: ExecutiveSnapshot" in models,
    "Executive snapshot is first-class Operations state",
)
check(
    '"executive": executive.to_dict()' in service
    and "executive=executive" in service,
    "Executive telemetry participates in aggregation and fingerprints",
)
check(
    "ExecutiveTelemetryAdapter" in public_api
    and "ExecutiveSnapshot" in public_api,
    "Stable public Executive telemetry imports",
)
check(
    'status: "/operations/status"' in bridge
    and "payload?.executive" in bridge,
    "Commander's Bridge consumes Operations Executive telemetry",
)
check(
    "/executive/" not in bridge
    and "executive_status" not in main_source,
    "No parallel Executive-status boundary",
)

contract_payload = {
    "model": "ExecutiveSnapshot",
    "operations_field": "executive",
    "endpoint": "/operations/status",
    "version": "genesis-vi-a1",
}
fingerprint = hashlib.sha256(
    json.dumps(
        contract_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()

print(f"[INFO] Contract fingerprint: {fingerprint}")
print("-" * 70)
print(f"Checks failed : {checks_failed}")
print(
    "Overall status: "
    + ("EXCELLENT" if checks_failed == 0 else "FAILED")
)
print("=" * 70)

return 0 if checks_failed == 0 else 1

if name == "main":
raise SystemExit(main())
EOF

cat > dev/verify_genesis_vi_a1.sh <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS — GENESIS VI-A1 EXECUTIVE TELEMETRY FOUNDATION"
echo "======================================================================"

"$PYTHON_BIN" -m compileall -q
core/operations
core/src/routes/operations.py

echo "[PASS] Genesis VI-A1 package compilation"

"$PYTHON_BIN" -m unittest
tests.test_mc1001_operations
tests.test_mc1002_commanders_bridge
tests.test_genesis_vi_a1_executive_telemetry

echo "[PASS] Genesis VI-A1 unit and regression tests"

"$PYTHON_BIN" dev/verification/verify_genesis_vi_a1.py

echo
echo "[PASS] Genesis VI-A1 Executive Telemetry Foundation"
EOF

chmod +x
dev/install_genesis_vi_a1.sh
dev/verify_genesis_vi_a1.sh
dev/verification/verify_genesis_vi_a1.py

echo "[PASS] Complete replacement files written"
echo "[PASS] Verification scripts made executable"

"$PYTHON_BIN" -m compileall -q
core/operations
core/src/routes/operations.py

echo "[PASS] Installation compilation"

echo
echo "Genesis VI-A1 installation completed."
echo "Run:"
echo
echo "PYTHON_BIN=$PYTHON_BIN ./dev/verify_genesis_vi_a1.sh"
echo
