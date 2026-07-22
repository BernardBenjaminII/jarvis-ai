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
