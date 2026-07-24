"""Real, read-only OperationsService capabilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.capabilities.base import Capability
from core.capabilities.metadata import (
    CapabilityMetadata,
    CapabilityOperation,
)
from core.capabilities.models import CapabilityContext, CapabilityResult
from core.capabilities.registry import CapabilityRegistry


class OperationsReadCapability(Capability):
    """Expose one real OperationsService read operation as a capability."""

    order = 100
    requires: set[str] = set()
    provides: set[str] = set()

    def __init__(
        self,
        *,
        name: str,
        display_name: str,
        description: str,
        provider_token: str,
        reader: Callable[[], Any],
    ) -> None:
        self.name = name
        self.provides = {provider_token}
        self._reader = reader
        self.metadata = CapabilityMetadata(
            display_name=display_name,
            description=description,
            domain="operations",
            subsystem="operations",
            operations=(
                CapabilityOperation(
                    name="read",
                    destructive=False,
                    supports_dry_run=False,
                    bound=True,
                ),
            ),
            tags=("read-only", "mission-control", "projection"),
            source="core.operations.OperationsService",
            version="mc1001",
        )

    @staticmethod
    def _serialize(value: Any) -> Any:
        if hasattr(value, "to_dict"):
            return value.to_dict()

        if isinstance(value, list):
            return [
                OperationsReadCapability._serialize(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                OperationsReadCapability._serialize(item)
                for item in value
            ]

        return value

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        try:
            value = self._serialize(self._reader())
            return CapabilityResult(
                name=self.name,
                success=True,
                output=value,
            )
        except TypeError:
            # Compatibility with older CapabilityResult contracts.
            result = CapabilityResult(name=self.name)
            if hasattr(result, "success"):
                object.__setattr__(result, "success", True)
            if hasattr(result, "output"):
                object.__setattr__(result, "output", value)
            return result


def register_operations_capabilities(
    registry: CapabilityRegistry,
    operations_service: Any,
) -> None:
    """Register canonical, non-destructive OperationsService capabilities."""

    event_registry = operations_service.event_registry

    capabilities = (
        OperationsReadCapability(
            name="operations.status",
            display_name="Operations Status",
            description="Read the canonical Operations snapshot.",
            provider_token="operations.status.read",
            reader=operations_service.snapshot,
        ),
        OperationsReadCapability(
            name="operations.executive",
            display_name="Executive Telemetry",
            description="Read the canonical Executive telemetry projection.",
            provider_token="operations.executive.read",
            reader=operations_service.executive,
        ),
        OperationsReadCapability(
            name="operations.health",
            display_name="Operations Health",
            description="Read Operations component health.",
            provider_token="operations.health.read",
            reader=operations_service.health,
        ),
        OperationsReadCapability(
            name="operations.missions",
            display_name="Mission Inventory",
            description="Read the currently projected missions.",
            provider_token="operations.missions.read",
            reader=operations_service.missions,
        ),
        OperationsReadCapability(
            name="operations.resources",
            display_name="Runtime Resources",
            description="Read current host and worker resource telemetry.",
            provider_token="operations.resources.read",
            reader=operations_service.resources,
        ),
        OperationsReadCapability(
            name="operations.timeline",
            display_name="Operations Timeline",
            description="Read the current Operations timeline.",
            provider_token="operations.timeline.read",
            reader=lambda: operations_service.timeline(limit=100),
        ),
        OperationsReadCapability(
            name="operations.events",
            display_name="Operations Events",
            description="Read the current Operations event registry.",
            provider_token="operations.events.read",
            reader=lambda: event_registry.list_events(limit=100),
        ),
    )

    existing = {
        capability.name
        for capability in registry.all()
    }

    for capability in capabilities:
        if capability.name not in existing:
            registry.register(capability)
            existing.add(capability.name)
