"""FastAPI routes for the MC-1001 Operations interface."""

from __future__ import annotations

from fastapi import APIRouter, Query

from core.operations import OperationsService

router = APIRouter(prefix="/operations", tags=["operations"])
_service = OperationsService()


def get_operations_service() -> OperationsService:
    """Return the process-wide Sprint 0 Operations service."""

    return _service


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


@router.get("/events")
def operations_events(
    limit: int = Query(default=100, ge=0, le=1000),
) -> list[dict]:
    return [
        event.to_dict()
        for event in get_operations_service().event_registry.list_events(limit=limit)
    ]
