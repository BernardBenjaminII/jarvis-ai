from __future__ import annotations

from core.capabilities import CapabilityLoader, CapabilityRegistry


def main() -> None:
    registry = CapabilityRegistry()

    loader = CapabilityLoader(
        package_roots=[
            "knowledge_engine.capabilities",
        ]
    )

    results = loader.load(registry)

    print("Load results:")
    for result in results:
        status = "OK" if result.loaded else "FAIL"
        print(f"{status}: {result.module}")
        if result.error:
            print(f"  {result.error}")

    capabilities = registry.all()

    print()
    print("Capabilities:")
    for capability in capabilities:
        print(
            f"- {capability.name} "
            f"requires={sorted(capability.requires)} "
            f"provides={sorted(capability.provides)}"
        )

    assert capabilities, "No capabilities loaded"
    assert any(c.name == "knowledge.chunking" for c in capabilities)
    assert any(c.name == "knowledge.embeddings" for c in capabilities)
    assert any(c.name == "knowledge.faiss" for c in capabilities)
    assert any(c.name == "knowledge.graph" for c in capabilities)

    print()
    print("Capability loader OK")


if __name__ == "__main__":
    main()
