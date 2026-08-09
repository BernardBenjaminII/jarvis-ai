
"""Deterministic capability dependency graph."""

from __future__ import annotations

from .registry import CapabilityRegistry


class CapabilityGraphError(RuntimeError):
    pass


class CapabilityGraph:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def dependencies_for(self, capability_id: str) -> tuple[str, ...]:
        return self._registry.get(capability_id).dependencies

    def validate(self) -> tuple[str, ...]:
        findings: list[str] = []
        known = {item.capability_id for item in self._registry.all()}
        for capability in self._registry.all():
            for dependency in capability.dependencies:
                if dependency not in known:
                    findings.append(
                        f"{capability.capability_id} requires missing dependency {dependency}."
                    )
        try:
            self.topological_order()
        except CapabilityGraphError as exc:
            findings.append(str(exc))
        return tuple(findings)

    def closure(self, capability_id: str) -> tuple[str, ...]:
        self._registry.get(capability_id)
        ordered: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(current: str) -> None:
            if current in visiting:
                raise CapabilityGraphError(f"Capability dependency cycle detected at {current}.")
            if current in visited:
                return
            visiting.add(current)
            for dependency in self.dependencies_for(current):
                visit(dependency)
            visiting.remove(current)
            visited.add(current)
            ordered.append(current)

        visit(capability_id)
        return tuple(ordered)

    def topological_order(self) -> tuple[str, ...]:
        ordered: list[str] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(capability_id: str) -> None:
            if capability_id in visiting:
                raise CapabilityGraphError(
                    f"Capability dependency cycle detected at {capability_id}."
                )
            if capability_id in visited:
                return
            visiting.add(capability_id)
            for dependency in self.dependencies_for(capability_id):
                self._registry.get(dependency)
                visit(dependency)
            visiting.remove(capability_id)
            visited.add(capability_id)
            ordered.append(capability_id)

        for capability in self._registry.all():
            visit(capability.capability_id)
        return tuple(ordered)
