from __future__ import annotations

from core.capabilities import (
    Capability,
    CapabilityContext,
    CapabilityRegistry,
    CapabilityResult,
    CapabilityRunner,
)


class DiscoveryCapability(Capability):
    name = "discovery"
    provides = {"discovery"}
    order = 10

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            name=self.name,
            metrics={"files_seen": 3},
        )


class ObjectCapability(Capability):
    name = "objects"
    requires = {"discovery"}
    provides = {"objects"}
    order = 20

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            name=self.name,
            metrics={"objects_built": 1},
        )


class GraphCapability(Capability):
    name = "graph"
    requires = {"objects"}
    provides = {"graph"}
    order = 30

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            name=self.name,
            metrics={"nodes": 2, "edges": 1},
        )


def main() -> None:
    registry = CapabilityRegistry()
    registry.register(GraphCapability())
    registry.register(ObjectCapability())
    registry.register(DiscoveryCapability())

    resolved = [cap.name for cap in registry.resolve()]
    assert resolved == ["discovery", "objects", "graph"], resolved

    results = CapabilityRunner(registry).run(CapabilityContext())
    assert all(result.success for result in results)
    assert [result.name for result in results] == ["discovery", "objects", "graph"]

    print("Capability framework OK")


if __name__ == "__main__":
    main()
