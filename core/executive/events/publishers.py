"""Publisher helpers for existing Executive services."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from core.executive.timeline import (
    TimelineContext,
    TimelineEventDraft,
    TimelineEventKind,
    TimelineSubsystem,
)

from .bus import ExecutiveEventBus
from .contracts import ExecutivePublication


class ExecutivePublisher:
    """Small constitutional adapter around ExecutiveEventBus."""

    def __init__(self, event_bus: ExecutiveEventBus) -> None:
        self._event_bus = event_bus

    @property
    def event_bus(self) -> ExecutiveEventBus:
        return self._event_bus

    def publish(
        self,
        *,
        subsystem: TimelineSubsystem,
        kind: TimelineEventKind,
        context: TimelineContext | None = None,
        payload: Mapping[str, object] | None = None,
        occurred_at: datetime | None = None,
        parent_event_id: str | None = None,
    ) -> ExecutivePublication:
        return self._event_bus.publish(
            TimelineEventDraft(
                subsystem=subsystem,
                kind=kind,
                context=context or TimelineContext(),
                payload=dict(payload or {}),
                occurred_at=occurred_at,
                parent_event_id=parent_event_id,
            )
        )


MISSION_EVENT_KINDS = {
    "mission_started": TimelineEventKind.MISSION_STARTED,
    "mission_completed": TimelineEventKind.MISSION_COMPLETED,
    "mission_failed": TimelineEventKind.MISSION_FAILED,
    "mission_blocked": TimelineEventKind.MISSION_BLOCKED,
    "mission_aborted": TimelineEventKind.MISSION_ABORTED,
    "task_started": TimelineEventKind.TASK_STARTED,
    "task_completed": TimelineEventKind.TASK_COMPLETED,
    "task_failed": TimelineEventKind.TASK_FAILED,
    "task_blocked": TimelineEventKind.TASK_BLOCKED,
}


class MissionEventPublisher(ExecutivePublisher):
    def publish_transition(
        self,
        *,
        mission_id: str,
        event_type: str,
        payload: Mapping[str, object],
        occurred_at: datetime,
    ) -> ExecutivePublication:
        try:
            kind = MISSION_EVENT_KINDS[event_type]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported Mission Engine event type: {event_type}"
            ) from exc

        task_id = payload.get("task_id")
        return self.publish(
            subsystem=TimelineSubsystem.MISSION,
            kind=kind,
            context=TimelineContext(
                mission_id=mission_id,
                task_id=str(task_id) if task_id else None,
                correlation_id=mission_id,
            ),
            payload={
                "legacy_event_type": event_type,
                **dict(payload),
            },
            occurred_at=occurred_at,
        )


class HealthEventPublisher(ExecutivePublisher):
    def publish_transition(
        self,
        *,
        previous_state: str | None,
        current_state: str,
        checked_at: datetime,
        components: int,
    ) -> ExecutivePublication:
        return self.publish(
            subsystem=TimelineSubsystem.HEALTH,
            kind=TimelineEventKind.HEALTH_STATE_CHANGED,
            payload={
                "previous_state": previous_state,
                "current_state": current_state,
                "component_count": components,
            },
            occurred_at=checked_at,
        )


class CapabilityEventPublisher(ExecutivePublisher):
    def registered(
        self,
        *,
        name: str,
        provides: list[str],
        requires: list[str],
        order: int,
    ) -> ExecutivePublication:
        return self.publish(
            subsystem=TimelineSubsystem.CAPABILITY,
            kind=TimelineEventKind.CAPABILITY_REGISTERED,
            payload={
                "name": name,
                "provides": provides,
                "requires": requires,
                "order": order,
            },
        )


class DirectorEventPublisher(ExecutivePublisher):
    def registered(
        self,
        *,
        name: str,
        capabilities: list[str],
        readiness: str,
        priority: int,
    ) -> ExecutivePublication:
        return self.publish(
            subsystem=TimelineSubsystem.DIRECTORATE,
            kind=TimelineEventKind.DIRECTOR_REGISTERED,
            payload={
                "name": name,
                "capabilities": capabilities,
                "readiness": readiness,
                "priority": priority,
            },
        )

    def unregistered(self, *, name: str) -> ExecutivePublication:
        return self.publish(
            subsystem=TimelineSubsystem.DIRECTORATE,
            kind=TimelineEventKind.DIRECTOR_UNREGISTERED,
            payload={"name": name},
        )

    def readiness_changed(
        self,
        *,
        name: str,
        previous_readiness: str,
        current_readiness: str,
    ) -> ExecutivePublication:
        return self.publish(
            subsystem=TimelineSubsystem.DIRECTORATE,
            kind=TimelineEventKind.DIRECTOR_READINESS_CHANGED,
            payload={
                "name": name,
                "previous_readiness": previous_readiness,
                "current_readiness": current_readiness,
            },
        )
