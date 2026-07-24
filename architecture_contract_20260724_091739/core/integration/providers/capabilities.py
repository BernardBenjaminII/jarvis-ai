"""Capability-registry projection provider."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.capabilities.base import Capability
from core.capabilities.metadata import (
    CapabilityBindingState,
    metadata_for,
)
from core.capabilities.registry import CapabilityRegistry
from core.integration.contracts import (
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)


class CapabilityProjectionProvider:
    projection_id = "capabilities"
    schema_version = "1.1"

    def __init__(
        self,
        registry: CapabilityRegistry,
        *,
        load_results: list[Any] | None = None,
    ) -> None:
        self.registry = registry
        self.load_results = list(load_results or [])

    def health(self) -> ProjectionHealth:
        failures = [
            result
            for result in self.load_results
            if not bool(getattr(result, "loaded", False))
        ]
        total = len(self.registry.all())

        if failures and total == 0:
            return ProjectionHealth(
                status=ProjectionStatus.UNAVAILABLE,
                summary="Capability discovery failed and no capabilities are registered.",
                details={
                    "registered_capabilities": 0,
                    "load_failures": len(failures),
                },
                errors=tuple(
                    f"{getattr(item, 'module', 'unknown')}: "
                    f"{getattr(item, 'error', 'unknown error')}"
                    for item in failures
                ),
            )

        if failures:
            return ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Capabilities are available with discovery failures.",
                details={
                    "registered_capabilities": total,
                    "load_failures": len(failures),
                },
                warnings=tuple(
                    f"{getattr(item, 'module', 'unknown')}: "
                    f"{getattr(item, 'error', 'unknown error')}"
                    for item in failures
                ),
            )

        if total == 0:
            return ProjectionHealth(
                status=ProjectionStatus.NOT_CONFIGURED,
                summary="No capabilities are registered.",
                details={"registered_capabilities": 0},
            )

        return ProjectionHealth(
            status=ProjectionStatus.AVAILABLE,
            summary="Capability registry is available.",
            details={
                "registered_capabilities": total,
                "provided_tokens": len(self.registry.provided_tokens()),
            },
        )

    @staticmethod
    def _qualified_type(value: object) -> str:
        cls = value.__class__
        return f"{cls.__module__}.{cls.__qualname__}"

    @staticmethod
    def _descriptor(capability: Capability) -> dict[str, Any]:
        metadata = metadata_for(capability)

        return {
            "id": capability.name,
            "name": capability.name,
            "display_name": metadata.display_name,
            "description": metadata.description,
            "domain": metadata.domain,
            "subsystem": metadata.subsystem,
            "implementation": CapabilityProjectionProvider._qualified_type(capability),
            "order": capability.order,
            "requires": sorted(capability.requires),
            "provides": sorted(capability.provides),
            "availability": metadata.binding_state.value,
            "bound": metadata.binding_state == CapabilityBindingState.BOUND,
            "operations": [
                operation.to_dict()
                for operation in metadata.operations
            ],
            "tags": list(metadata.tags),
            "source": metadata.source,
            "version": metadata.version,
        }

    def project(self) -> ProjectionEnvelope:
        generated_at = datetime.now(timezone.utc)
        capabilities = sorted(
            (
                self._descriptor(capability)
                for capability in self.registry.all()
            ),
            key=lambda item: (item["order"], item["id"]),
        )

        resolution: dict[str, Any]
        warnings: tuple[str, ...] = ()

        try:
            execution_order = [
                capability.name
                for capability in self.registry.resolve()
            ]
            resolution = {
                "resolvable": True,
                "execution_order": execution_order,
                "blocked": {},
            }
        except RuntimeError as exc:
            execution_order = []
            resolution = {
                "resolvable": False,
                "execution_order": [],
                "blocked": {"message": str(exc)},
            }
            warnings = (str(exc),)

        bound_count = sum(
            1 for capability in capabilities
            if capability["bound"]
        )

        health = self.health()

        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=generated_at,
            source_timestamp=None,
            provider=self._qualified_type(self),
            health=health,
            data={
                "total": len(capabilities),
                "bound": bound_count,
                "unbound": len(capabilities) - bound_count,
                "provided_tokens": sorted(self.registry.provided_tokens()),
                "capabilities": capabilities,
                "dependency_resolution": resolution,
                "discovery": {
                    "configured_package_roots": sorted({
                        getattr(result, "module", "").split(".")[0]
                        for result in self.load_results
                        if getattr(result, "module", "")
                    }),
                    "modules_examined": len(self.load_results),
                    "modules_with_hooks": sum(
                        1 for result in self.load_results
                        if bool(getattr(result, "discovered", False))
                    ),
                    "registered_from_hooks": sum(
                        int(getattr(result, "registered_count", 0))
                        for result in self.load_results
                    ),
                },
                "load_results": [
                    {
                        "module": getattr(result, "module", "unknown"),
                        "discovered": bool(
                            getattr(result, "discovered", False)
                        ),
                        "loaded": bool(getattr(result, "loaded", False)),
                        "registered_count": int(
                            getattr(result, "registered_count", 0)
                        ),
                        "error": getattr(result, "error", None),
                    }
                    for result in self.load_results
                ],
            },
            warnings=warnings,
        )
