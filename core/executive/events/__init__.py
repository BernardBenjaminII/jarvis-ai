"""Canonical Executive Event Bus integration."""
from .bus import ExecutiveEventBus, ExecutiveSubscription
from .contracts import (
    ExecutiveEventSubscriber,
    ExecutivePublication,
    ExecutiveSubscriberFailure,
)
from .integration import ExecutiveLiveEventBridge, timeline_event_payload
from .runtime import (
    build_executive_event_bus,
    get_default_executive_event_bus,
    reset_default_executive_event_bus,
    resolve_default_timeline_root,
)

__all__ = [
    "ExecutiveEventBus",
    "ExecutiveEventSubscriber",
    "ExecutiveLiveEventBridge",
    "ExecutivePublication",
    "ExecutiveSubscriberFailure",
    "ExecutiveSubscription",
    "build_executive_event_bus",
    "get_default_executive_event_bus",
    "reset_default_executive_event_bus",
    "resolve_default_timeline_root",
    "timeline_event_payload",
]
