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


# JARVIS_SPACE_R89A_IMPORT
from core.space_monitor.satellites import (
    satellite_snapshot,
    satellite_health,
    satellite_orbit_track,

    satellite_pass_prediction,
    satellites_above_observer,)

# JARVIS_SPACE_R87_IMPORT
from core.space_monitor.service import (
    build_space_weather_snapshot,
    space_monitor_health,
)

router = APIRouter(prefix="/operations", tags=["operations"])

# JARVIS_SPACE_R87_ROUTES_START

@router.get("/space")
def get_space_monitor():
    """
    Jarvis Space Monitor root manifest.

    R8.7 provides authoritative NOAA SWPC space-weather data.
    R8.8+ will add NEO and orbital monitoring without changing
    this root contract.
    """
    health = space_monitor_health()

    return {
        "schema": "jarvis.space.r8.7",
        "status": health["status"],
        "sources_ok": health["sources_ok"],
        "sources_total": health["sources_total"],
        "capabilities": {
            "space_weather": True,
            "near_earth_objects": False,
            "orbital_objects": False,
            "local_rf_sensor": False,
        },
        "endpoints": {
            "weather": "/operations/space/weather",
            "aurora": "/operations/space/weather/aurora",
            "health": "/operations/space/health",
        },
    }


@router.get("/space/weather")
def get_space_weather():
    """
    Current normalized NOAA SWPC space-weather snapshot.
    """
    return build_space_weather_snapshot()


@router.get("/space/weather/aurora")
def get_space_aurora():
    """
    Current NOAA OVATION auroral probability grid.

    Kept as a separate endpoint because the full coordinate
    set is much larger than the normal weather summary.
    """
    snapshot = build_space_weather_snapshot()

    return {
        "schema": "jarvis.space.aurora.r8.7",
        "generated_at": snapshot["generated_at"],
        "aurora": snapshot["aurora"],
        "source": next(
            (
                source
                for source in snapshot["sources"]
                if source["name"] == "aurora"
            ),
            None,
        ),
    }


@router.get("/space/health")
def get_space_health():
    """
    Health/status of authoritative remote space sources.
    """
    return space_monitor_health()

# JARVIS_SPACE_R87_ROUTES_END

# JARVIS_SPACE_R89A_ROUTES

@router.get("/space/satellites")
def get_space_satellites(
    groups: str | None = None,
):
    """
    Current propagated locations for useful satellite groups.

    groups:
        stations,gps,weather
    """

    selected = None

    if groups:
        selected = [
            value.strip()
            for value in groups.split(",")
            if value.strip()
        ]

    try:
        return satellite_snapshot(
            selected
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/space/satellites/health")
def get_space_satellite_health():
    return satellite_health()




# JARVIS_SPACE_R89D_ROUTES

@router.get("/space/observer")
def get_space_observer(
    lat: float,
    lon: float,
    alt_m: float = 0.0,
    min_elevation_deg: float = 0.0,
):
    if not -90.0 <= lat <= 90.0:
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90",
        )

    if not -180.0 <= lon <= 180.0:
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180",
        )

    return satellites_above_observer(
        observer_latitude=lat,
        observer_longitude=lon,
        observer_altitude_m=alt_m,
        min_elevation_deg=min_elevation_deg,
    )


@router.get("/space/satellites/{norad_id}/pass")
def get_space_satellite_pass(
    norad_id: int,
    lat: float,
    lon: float,
    alt_m: float = 0.0,
    hours: float = 24.0,
    min_elevation_deg: float = 0.0,
):
    if not -90.0 <= lat <= 90.0:
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90",
        )

    if not -180.0 <= lon <= 180.0:
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180",
        )

    try:
        return satellite_pass_prediction(
            norad_id=norad_id,
            observer_latitude=lat,
            observer_longitude=lon,
            observer_altitude_m=alt_m,
            hours=hours,
            min_elevation_deg=min_elevation_deg,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


# JARVIS_SPACE_R89C_ROUTES

@router.get("/space/satellites/{norad_id}/track")
def get_space_satellite_track(
    norad_id: int,
    minutes_back: int = 45,
    minutes_forward: int = 45,
):
    """
    Return a short propagated orbit/ground track for one selected satellite.
    """

    minutes_back = max(
        0,
        min(minutes_back, 180),
    )

    minutes_forward = max(
        0,
        min(minutes_forward, 180),
    )

    try:
        return satellite_orbit_track(
            norad_id,
            minutes_back=minutes_back,
            minutes_forward=minutes_forward,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc



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
    return get_sitrep_service().snapshot_background(force_refresh=refresh)




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
