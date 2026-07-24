"""Process-wide bootstrap for the Executive Integration Plane."""

from __future__ import annotations

import os
from dataclasses import dataclass

from core.capabilities.discovery import (
    CapabilityDiscovery,
    CapabilityDiscoveryResult,
)
from core.capabilities.operations import register_operations_capabilities
from core.capabilities.registry import CapabilityRegistry
from core.integration.knowledge_inventory import KnowledgeInventoryService
from core.integration.providers.capabilities import CapabilityProjectionProvider
from core.integration.providers.knowledge import KnowledgeProjectionProvider
from core.integration.providers.operations import OperationsProjectionProvider
from core.integration.registry import ProjectionRegistry
from core.integration.service import ExecutiveProjectionService
from core.operations import OperationsService


@dataclass(frozen=True)
class ExecutiveIntegrationRuntime:
    operations_service: OperationsService
    capability_registry: CapabilityRegistry
    knowledge_inventory_service: KnowledgeInventoryService
    projection_registry: ProjectionRegistry
    projection_service: ExecutiveProjectionService
    capability_load_results: tuple[CapabilityDiscoveryResult, ...]


def _configured_capability_packages() -> list[str]:
    raw = os.getenv("JARVIS_CAPABILITY_PACKAGES", "")
    return [
        value.strip()
        for value in raw.split(",")
        if value.strip()
    ]


def build_default_integration_runtime(
    *,
    operations_service: OperationsService | None = None,
    capability_packages: list[str] | None = None,
    knowledge_inventory_service: KnowledgeInventoryService | None = None,
) -> ExecutiveIntegrationRuntime:
    operations = operations_service or OperationsService()
    capabilities = CapabilityRegistry()
    knowledge_inventory = (
        knowledge_inventory_service
        or KnowledgeInventoryService()
    )

    register_operations_capabilities(capabilities, operations)

    package_roots = (
        list(capability_packages)
        if capability_packages is not None
        else _configured_capability_packages()
    )

    load_results = (
        CapabilityDiscovery(package_roots).discover(capabilities)
        if package_roots
        else []
    )

    projections = ProjectionRegistry()
    projections.register(OperationsProjectionProvider(operations))
    projections.register(
        CapabilityProjectionProvider(
            capabilities,
            load_results=load_results,
        )
    )
    projections.register(
        KnowledgeProjectionProvider(knowledge_inventory)
    )

    return ExecutiveIntegrationRuntime(
        operations_service=operations,
        capability_registry=capabilities,
        knowledge_inventory_service=knowledge_inventory,
        projection_registry=projections,
        projection_service=ExecutiveProjectionService(projections),
        capability_load_results=tuple(load_results),
    )


_DEFAULT_RUNTIME: ExecutiveIntegrationRuntime | None = None


def get_default_integration_runtime() -> ExecutiveIntegrationRuntime:
    global _DEFAULT_RUNTIME

    if _DEFAULT_RUNTIME is None:
        _DEFAULT_RUNTIME = build_default_integration_runtime()

    return _DEFAULT_RUNTIME


def reset_default_integration_runtime() -> None:
    global _DEFAULT_RUNTIME
    _DEFAULT_RUNTIME = None
