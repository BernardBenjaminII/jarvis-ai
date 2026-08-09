
"""Canonical additive registry for Executive capability orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import CapabilityHealth, CapabilityMetadata


class CapabilityRegistry:
    def __init__(self, capabilities: Iterable[CapabilityMetadata] = ()) -> None:
        self._capabilities: dict[str, CapabilityMetadata] = {}
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: CapabilityMetadata, *, replace_existing: bool = False) -> None:
        existing = self._capabilities.get(capability.capability_id)
        if existing is not None and not replace_existing:
            raise ValueError(f"Capability already registered: {capability.capability_id}")
        self._capabilities[capability.capability_id] = capability

    def get(self, capability_id: str) -> CapabilityMetadata:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise KeyError(f"Unknown capability: {capability_id}") from exc

    def all(self) -> tuple[CapabilityMetadata, ...]:
        return tuple(self._capabilities[key] for key in sorted(self._capabilities))

    def update_health(self, capability_id: str, health: CapabilityHealth) -> CapabilityMetadata:
        capability = replace(self.get(capability_id), health=health)
        self._capabilities[capability_id] = capability
        return capability

    def by_mission_type(self, mission_type: str) -> tuple[CapabilityMetadata, ...]:
        return tuple(
            capability
            for capability in self.all()
            if mission_type in capability.mission_types
        )

    def __len__(self) -> int:
        return len(self._capabilities)
