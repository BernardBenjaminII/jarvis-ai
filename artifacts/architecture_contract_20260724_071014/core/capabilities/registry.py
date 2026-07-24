from __future__ import annotations

from core.capabilities.base import Capability


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability already registered: {capability.name}")

        self._capabilities[capability.name] = capability

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
        """
        Resolve capabilities by declared requirements.

        A capability can run when all required tokens have already been provided.
        Falls back to order when several are available.
        """

        remaining = set(self._capabilities.keys())
        provided: set[str] = set()
        resolved: list[Capability] = []

        while remaining:
            runnable = []

            for name in remaining:
                capability = self._capabilities[name]
                if capability.requires <= provided:
                    runnable.append(capability)

            if not runnable:
                blocked = {
                    name: sorted(self._capabilities[name].requires - provided)
                    for name in sorted(remaining)
                }
                raise RuntimeError(f"Unresolved capability dependencies: {blocked}")

            runnable.sort(key=lambda c: (c.order, c.name))

            for capability in runnable:
                resolved.append(capability)
                provided.update(capability.provides)
                remaining.remove(capability.name)

        return resolved
