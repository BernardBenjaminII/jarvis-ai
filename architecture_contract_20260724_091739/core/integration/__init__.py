"""Stable public Executive Integration API."""
from __future__ import annotations
from core.integration.bootstrap import build_default_integration_runtime, get_default_integration_runtime
from core.integration.bus import ExecutiveProjectionBus, ProjectionBusSnapshot, get_default_projection_bus, reset_default_projection_bus
from core.integration.readiness import ExecutiveReadiness, ReadinessColor, ReadinessLevel, normalize_projection_readiness
from core.integration import contracts as _contracts
from core.integration import registry as _registry
from core.integration import service as _service

def _export_public(module) -> list[str]:
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in vars(module) if not name.startswith("_")]
    exported = []
    for name in names:
        if hasattr(module, name):
            globals()[name] = getattr(module, name)
            exported.append(name)
    return exported

__all__ = sorted(set(
    _export_public(_contracts) + _export_public(_registry) + _export_public(_service) + [
        "ExecutiveProjectionBus", "ExecutiveReadiness", "ProjectionBusSnapshot",
        "ReadinessColor", "ReadinessLevel", "build_default_integration_runtime",
        "get_default_integration_runtime", "get_default_projection_bus",
        "normalize_projection_readiness", "reset_default_projection_bus",
    ]
))
