"""Stable metadata contracts for capability discovery and projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityBindingState(str, Enum):
    BOUND = "bound"
    UNBOUND = "unbound"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class CapabilityOperation:
    name: str
    destructive: bool = False
    supports_dry_run: bool = False
    bound: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "destructive": self.destructive,
            "supports_dry_run": self.supports_dry_run,
            "bound": self.bound,
        }


@dataclass(frozen=True)
class CapabilityMetadata:
    display_name: str
    description: str
    domain: str
    subsystem: str
    binding_state: CapabilityBindingState = CapabilityBindingState.BOUND
    operations: tuple[CapabilityOperation, ...] = field(
        default_factory=lambda: (CapabilityOperation(name="execute"),)
    )
    tags: tuple[str, ...] = ()
    source: str = "runtime"
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "description": self.description,
            "domain": self.domain,
            "subsystem": self.subsystem,
            "binding_state": self.binding_state.value,
            "operations": [
                operation.to_dict()
                for operation in self.operations
            ],
            "tags": list(self.tags),
            "source": self.source,
            "version": self.version,
        }


def metadata_for(capability: object) -> CapabilityMetadata:
    metadata = getattr(capability, "metadata", None)

    if isinstance(metadata, CapabilityMetadata):
        return metadata

    name = str(getattr(capability, "name", capability.__class__.__name__))

    return CapabilityMetadata(
        display_name=name,
        description="Capability registered without extended metadata.",
        domain="unknown",
        subsystem="unknown",
        source=f"{capability.__class__.__module__}.{capability.__class__.__qualname__}",
    )
