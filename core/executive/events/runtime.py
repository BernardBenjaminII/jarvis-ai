"""Lazy process-wide Executive Event Bus runtime."""
from __future__ import annotations

import os
from pathlib import Path
from threading import RLock

from core.executive.timeline import ExecutiveTimelineRepository

from .bus import ExecutiveEventBus

_DEFAULT_ENVIRONMENT_VARIABLE = "JARVIS_EXECUTIVE_TIMELINE_ROOT"
_DEFAULT_RELATIVE_ROOT = Path("artifacts/runtime/executive_timeline")

_lock = RLock()
_default_bus: ExecutiveEventBus | None = None


def resolve_default_timeline_root() -> Path:
    configured = os.environ.get(_DEFAULT_ENVIRONMENT_VARIABLE)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / _DEFAULT_RELATIVE_ROOT).resolve()


def build_executive_event_bus(root: str | Path) -> ExecutiveEventBus:
    return ExecutiveEventBus(
        repository=ExecutiveTimelineRepository(root)
    )


def get_default_executive_event_bus() -> ExecutiveEventBus:
    global _default_bus
    with _lock:
        if _default_bus is None:
            _default_bus = build_executive_event_bus(
                resolve_default_timeline_root()
            )
        return _default_bus


def reset_default_executive_event_bus() -> None:
    global _default_bus
    with _lock:
        _default_bus = None
