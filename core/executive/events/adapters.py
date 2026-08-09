"""Subscribers preserving legacy event consumers during migration."""
from __future__ import annotations

from typing import Protocol

from core.executive.timeline import TimelineEvent, TimelineSubsystem


class LegacyMissionEventStore(Protocol):
    def record_event(
        self,
        mission_id: str,
        event_type: str,
        payload: dict,
        occurred_at,
    ) -> None:
        ...


class MissionStoreEventSubscriber:
    """Mirror committed mission events into the legacy MissionStore view."""

    def __init__(self, store: LegacyMissionEventStore) -> None:
        self._store = store

    def __call__(self, event: TimelineEvent) -> None:
        if event.subsystem is not TimelineSubsystem.MISSION:
            return

        mission_id = event.context.mission_id
        if not mission_id:
            return

        payload = dict(event.payload)
        event_type = str(
            payload.pop("legacy_event_type", event.kind.value)
        )
        self._store.record_event(
            mission_id,
            event_type,
            payload,
            event.occurred_at,
        )
