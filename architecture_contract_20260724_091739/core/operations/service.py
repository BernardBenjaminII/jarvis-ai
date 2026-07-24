"""Canonical aggregation service for JARVIS operational state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from .enums import AlertSeverity, ExecutiveState, HealthState, OperationalState
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
        state = self._operational_state(
            health_state=health.state,
            executive_state=executive.state,
        )

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
    def _operational_state(
        *,
        health_state: HealthState,
        executive_state: ExecutiveState,
    ) -> OperationalState:
        if executive_state is ExecutiveState.STOPPED:
            return OperationalState.STOPPED
        if executive_state is ExecutiveState.PAUSED:
            return OperationalState.PAUSED
        if (
            health_state is HealthState.UNAVAILABLE
            or executive_state is ExecutiveState.FAILED
        ):
            return OperationalState.FAILED
        if (
            health_state in (HealthState.DEGRADED, HealthState.UNKNOWN)
            or executive_state is ExecutiveState.DEGRADED
        ):
            return OperationalState.DEGRADED
        if executive_state is ExecutiveState.INITIALIZING:
            return OperationalState.INITIALIZING
        return OperationalState.READY

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
