from __future__ import annotations

from core.capabilities.registry import CapabilityRegistry
from knowledge_engine.capabilities.registry import build_knowledge_registry


def register_capabilities(registry: CapabilityRegistry) -> None:
    knowledge_registry = build_knowledge_registry()

    for capability in knowledge_registry.all():
        registry.register(capability)
