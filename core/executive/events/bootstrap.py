"""Executive Event Runtime bootstrap and FastAPI lifespan integration."""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator

from fastapi import FastAPI

from core.executive.operations_center.transport import ExecutiveLiveBroker
from core.executive.timeline import (
    TimelineEventDraft,
    TimelineEventKind,
    TimelineSubsystem,
)

from .bus import ExecutiveEventBus
from .integration import ExecutiveLiveEventBridge
from .runtime import get_default_executive_event_bus


class ExecutiveEventRuntimeState(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExecutiveEventRuntimeSnapshot:
    state: ExecutiveEventRuntimeState
    event_count: int
    subscriber_count: int
    bridge_active: bool
    timeline_storage_path: str
    integrity_certified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "event_count": self.event_count,
            "subscriber_count": self.subscriber_count,
            "bridge_active": self.bridge_active,
            "timeline_storage_path": self.timeline_storage_path,
            "integrity_certified": self.integrity_certified,
        }


class ExecutiveEventRuntime:
    """Own one process-wide Event Bus and its live-transport bridge."""

    def __init__(
        self,
        *,
        event_bus: ExecutiveEventBus,
        live_broker: ExecutiveLiveBroker,
    ) -> None:
        self.event_bus = event_bus
        self.live_broker = live_broker
        self.live_bridge = ExecutiveLiveEventBridge(
            event_bus=event_bus,
            live_broker=live_broker,
        )
        self.state = ExecutiveEventRuntimeState.CREATED

    async def start(self) -> None:
        if self.state is ExecutiveEventRuntimeState.RUNNING:
            return
        if self.state is ExecutiveEventRuntimeState.STARTING:
            return

        self.state = ExecutiveEventRuntimeState.STARTING
        try:
            self.live_bridge.start()
            self.event_bus.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.EXECUTIVE,
                    kind=TimelineEventKind.EXECUTIVE_BOOT_STARTED,
                    payload={
                        "component": "executive_event_runtime",
                        "transport": "websocket",
                    },
                )
            )
            self.state = ExecutiveEventRuntimeState.RUNNING
            self.event_bus.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.EXECUTIVE,
                    kind=TimelineEventKind.EXECUTIVE_BOOT_COMPLETED,
                    payload={
                        "component": "executive_event_runtime",
                        "integrity_certified": (
                            self.event_bus.verify().certified
                        ),
                    },
                )
            )
        except Exception:
            self.state = ExecutiveEventRuntimeState.FAILED
            self.live_bridge.stop()
            raise

    async def stop(self) -> None:
        if self.state in {
            ExecutiveEventRuntimeState.CREATED,
            ExecutiveEventRuntimeState.STOPPED,
        }:
            self.state = ExecutiveEventRuntimeState.STOPPED
            return

        self.state = ExecutiveEventRuntimeState.STOPPING
        try:
            self.event_bus.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.EXECUTIVE,
                    kind=TimelineEventKind.EXECUTIVE_SHUTDOWN_STARTED,
                    payload={
                        "component": "executive_event_runtime",
                    },
                )
            )
            self.event_bus.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.EXECUTIVE,
                    kind=TimelineEventKind.EXECUTIVE_SHUTDOWN_COMPLETED,
                    payload={
                        "component": "executive_event_runtime",
                    },
                )
            )
        finally:
            self.live_bridge.stop()
            self.state = ExecutiveEventRuntimeState.STOPPED

    def snapshot(self) -> ExecutiveEventRuntimeSnapshot:
        integrity = self.event_bus.verify()
        return ExecutiveEventRuntimeSnapshot(
            state=self.state,
            event_count=len(self.event_bus.events),
            subscriber_count=self.event_bus.subscriber_count,
            bridge_active=self.live_bridge.active,
            timeline_storage_path=str(
                self.event_bus.repository.storage_path
            ),
            integrity_certified=integrity.certified,
        )


def resolve_operations_live_broker(
    operations_runtime: Any,
) -> ExecutiveLiveBroker:
    """
    Resolve the existing Operations Center broker without coupling Pack 4A-3
    to one internal attribute name.
    """
    for attribute in ("broker", "live_broker", "_broker"):
        candidate = getattr(operations_runtime, attribute, None)
        if isinstance(candidate, ExecutiveLiveBroker):
            return candidate

    raise RuntimeError(
        "Executive Operations runtime exposes no ExecutiveLiveBroker."
    )


def build_executive_event_runtime(
    *,
    live_broker: ExecutiveLiveBroker,
    event_bus: ExecutiveEventBus | None = None,
) -> ExecutiveEventRuntime:
    return ExecutiveEventRuntime(
        event_bus=event_bus or get_default_executive_event_bus(),
        live_broker=live_broker,
    )


def install_executive_event_runtime(
    app: FastAPI,
    runtime: ExecutiveEventRuntime,
) -> None:
    """Expose the canonical runtime through FastAPI application state."""
    app.state.executive_event_runtime = runtime
    app.state.executive_event_bus = runtime.event_bus
    app.state.executive_timeline_repository = runtime.event_bus.repository


@asynccontextmanager
async def executive_application_lifespan(
    app: FastAPI,
    *,
    runtime: ExecutiveEventRuntime,
) -> AsyncIterator[None]:
    install_executive_event_runtime(app, runtime)
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()
