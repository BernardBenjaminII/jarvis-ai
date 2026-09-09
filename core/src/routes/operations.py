"""FastAPI routes for the MC-1001 Operations interface."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core.integration.bootstrap import get_default_integration_runtime
from core.integration.bus import get_default_projection_bus
from core.integration.errors import ProjectionProviderNotFoundError
from core.operations import OperationsService
from core.observability import get_default_observability_service
from core.sitrep import get_sitrep_service

router = APIRouter(prefix="/operations", tags=["operations"])
_service = OperationsService()


def get_operations_service() -> OperationsService:
    """Return the process-wide Sprint 0 Operations service."""

    return _service


def get_projection_service():
    """Return the canonical Executive Integration projection service."""

    return get_default_integration_runtime().projection_service


def get_capability_registry():
    """Return the canonical process-wide capability registry."""

    return get_default_integration_runtime().capability_registry


def get_projection_bus():
    """Return the canonical Executive Projection Bus."""

    return get_default_projection_bus()


@router.get("/status")
def operations_status() -> dict:
    return get_operations_service().snapshot().to_dict()


@router.get("/executive")
def operations_executive() -> dict:
    """Return the canonical Executive telemetry projection."""

    return get_operations_service().executive().to_dict()


@router.get("/health")
def operations_health() -> dict:
    return get_operations_service().health().to_dict()


@router.get("/missions")
def operations_missions() -> list[dict]:
    return [
        mission.to_dict()
        for mission in get_operations_service().missions()
    ]


@router.get("/resources")
def operations_resources() -> dict:
    return get_operations_service().resources().to_dict()


@router.get("/timeline")
def operations_timeline(
    limit: int = Query(default=100, ge=0, le=1000),
) -> dict:
    return get_operations_service().timeline(limit=limit).to_dict()

@router.get("/sitrep")
def operations_sitrep(refresh: bool = Query(default=False)) -> dict[str, Any]:
    """Return authoritative read-only SITREP records and source health."""
    return get_sitrep_service().snapshot(force_refresh=refresh)




@router.get("/transparency")
def operations_transparency() -> dict[str, Any]:
    """Return the latest UI-safe Executive mission-transparency projection."""

    snapshot = get_default_observability_service().latest()
    if snapshot is None:
        return {
            "status": "idle",
            "detail": "No converged Executive conversation has been observed yet.",
            "data": None,
        }
    return {"status": "ready", "data": snapshot.to_dict()}

@router.get("/events")
def operations_events(
    limit: int = Query(default=100, ge=0, le=1000),
) -> list[dict]:
    return [
        event.to_dict()
        for event in get_operations_service().event_registry.list_events(limit=limit)
    ]


# ---------------------------------------------------------------------------
# UI-A2 compatibility routes
# ---------------------------------------------------------------------------

@router.get("/projections")
def operations_projections() -> dict[str, Any]:
    """Return all canonical Executive Integration projections.

    This route preserves the Genesis UI-A2 public API while delegating to the
    current projection service. It is intentionally additive to VI-A3's Bridge.
    """

    return get_projection_service().all_projections()


@router.get("/projections/{projection_id}")
def operations_projection(projection_id: str) -> dict[str, Any]:
    """Return one canonical Executive Integration projection."""

    try:
        return get_projection_service().projection(projection_id).to_dict()
    except ProjectionProviderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown projection: {projection_id}",
        ) from exc


@router.get("/capabilities")
def operations_capabilities() -> dict[str, Any]:
    """Return the canonical capability projection."""

    return operations_projection("capabilities")


@router.get("/capabilities/{capability_name}")
def operations_capability(capability_name: str) -> dict[str, Any]:
    """Return one capability descriptor from the canonical registry projection."""

    envelope = operations_capabilities()
    capabilities = envelope.get("data", {}).get("capabilities", [])

    for capability in capabilities:
        if capability.get("id") == capability_name or capability.get("name") == capability_name:
            return capability

    raise HTTPException(
        status_code=404,
        detail=f"Unknown capability: {capability_name}",
    )


# ---------------------------------------------------------------------------
# VI-A3 Executive Projection Bus routes
# ---------------------------------------------------------------------------

@router.get("/bridge")
def executive_bridge_snapshot() -> dict:
    return get_projection_bus().snapshot().to_dict()


@router.get("/bridge/readiness")
def executive_bridge_readiness() -> dict:
    return get_projection_bus().readiness()


@router.get("/bridge/manifest")
def executive_bridge_manifest() -> dict:
    return get_projection_bus().manifest()


@router.get("/bridge/projections/{projection_id}")
def executive_bridge_projection(projection_id: str) -> dict:
    projection = get_projection_bus().projection(projection_id)
    if projection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown projection: {projection_id}",
        )
    return dict(projection)

# Genesis IX-A4.7 Pack 3 — grounded answer telemetry route
@router.get("/executive/grounded-answer")
def operations_grounded_answer_telemetry() -> dict[str, Any]:
    from core.conversation.grounded_answer.telemetry import get_grounded_answer_telemetry_store
    return get_grounded_answer_telemetry_store().projection()
