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
