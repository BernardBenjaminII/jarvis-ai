from __future__ import annotations

from core.capabilities.base import Capability
from core.executive.events import (
    CapabilityEventPublisher,
    ExecutiveEventBus,
)


class CapabilityRegistry:
    def __init__(
        self,
        *,
        event_bus: ExecutiveEventBus | None = None,
    ) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._publisher = (
            CapabilityEventPublisher(event_bus)
            if event_bus is not None
            else None
        )

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(
                f"Capability already registered: {capability.name}"
            )

        self._capabilities[capability.name] = capability

        if self._publisher is not None:
            self._publisher.registered(
                name=capability.name,
                provides=sorted(capability.provides),
                requires=sorted(capability.requires),
                order=capability.order,
            )

    def get(self, name: str) -> Capability:
        return self._capabilities[name]

    def all(self) -> list[Capability]:
        return list(self._capabilities.values())

    def provided_tokens(self) -> set[str]:
        provided: set[str] = set()
        for capability in self._capabilities.values():
            provided.update(capability.provides)
        return provided

    def resolve(self) -> list[Capability]:
        remaining = set(self._capabilities.keys())
        provided: set[str] = set()
        resolved: list[Capability] = []

        while remaining:
            runnable = [
                self._capabilities[name]
                for name in remaining
                if self._capabilities[name].requires <= provided
            ]

            if not runnable:
                blocked = {
                    name: sorted(
                        self._capabilities[name].requires - provided
                    )
                    for name in sorted(remaining)
                }
                raise RuntimeError(
                    f"Unresolved capability dependencies: {blocked}"
                )

            runnable.sort(key=lambda item: (item.order, item.name))

            for capability in runnable:
                resolved.append(capability)
                provided.update(capability.provides)
                remaining.remove(capability.name)

        return resolved
