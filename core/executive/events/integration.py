"""Adapters from constitutional events to existing Executive transports."""
from __future__ import annotations

import asyncio
from typing import Any

from core.executive.operations_center.transport import (
    ExecutiveLiveBroker,
    ExecutiveLiveEnvelope,
)
from core.executive.timeline import TimelineEvent

from .bus import ExecutiveEventBus, ExecutiveSubscription


def timeline_event_payload(event: TimelineEvent) -> dict[str, Any]:
    return {
        **event.material(),
        "event_fingerprint": event.event_fingerprint,
    }


class ExecutiveLiveEventBridge:
    """Forward committed Executive events into the existing live broker."""

    def __init__(
        self,
        *,
        event_bus: ExecutiveEventBus,
        live_broker: ExecutiveLiveBroker,
    ) -> None:
        self._event_bus = event_bus
        self._live_broker = live_broker
        self._subscription: ExecutiveSubscription | None = None

    @property
    def active(self) -> bool:
        return self._subscription is not None

    def start(self) -> None:
        if self.active:
            return
        self._subscription = self._event_bus.subscribe(
            self._forward,
            name="executive-live-event-bridge",
        )

    def stop(self) -> None:
        if self._subscription is None:
            return
        self._event_bus.unsubscribe(self._subscription)
        self._subscription = None

    def _forward(self, event: TimelineEvent) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        envelope = ExecutiveLiveEnvelope.create(
            message_type="executive.event",
            payload=timeline_event_payload(event),
        )
        loop.create_task(self._live_broker.publish(envelope))
