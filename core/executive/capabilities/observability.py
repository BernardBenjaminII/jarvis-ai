
"""Read-only observability projection for Mission Control integration."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .registry import CapabilityRegistry


class CapabilityObservabilityService:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> dict[str, Any]:
        capabilities = self._registry.all()
        health_counts = Counter(item.health.value for item in capabilities)
        return {
            "schema_version": "1.0.0",
            "pack": "Genesis VII-A0 Pack 4B-2",
            "capability_count": len(capabilities),
            "health": {
                key: health_counts.get(key, 0)
                for key in (
                    "ready",
                    "busy",
                    "degraded",
                    "failed",
                    "disabled",
                    "unknown",
                )
            },
            "capabilities": [item.to_dict() for item in capabilities],
        }
