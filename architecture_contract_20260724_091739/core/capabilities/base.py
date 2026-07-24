from __future__ import annotations

from abc import ABC, abstractmethod

from core.capabilities.models import CapabilityContext, CapabilityResult


class Capability(ABC):
    name: str = "unnamed"
    description: str = ""
    requires: set[str] = set()
    provides: set[str] = set()
    order: int = 1000

    @abstractmethod
    def execute(self, context: CapabilityContext) -> CapabilityResult:
        ...
