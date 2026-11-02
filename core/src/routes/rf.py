"""JARVIS receive-only RF task API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.rf.dual_controller import PRIMARY, get_dual_rf_controller
from core.rf.models import (
    RFStatus,
    RFTaskDescriptor,
    RFTaskRequest,
)


router = APIRouter(
    prefix="/api/rf",
    tags=["RF"],
)


@router.get(
    "/status",
    response_model=RFStatus,
)
def rf_status() -> RFStatus:
    return get_dual_rf_controller()._get(PRIMARY).status()


@router.get(
    "/tasks",
    response_model=list[RFTaskDescriptor],
)
def rf_tasks() -> list[RFTaskDescriptor]:
    return get_dual_rf_controller()._get(PRIMARY).tasks()


@router.post(
    "/task/start",
    response_model=RFStatus,
)
def rf_start(
    request: RFTaskRequest,
) -> RFStatus:
    return get_dual_rf_controller()._get(PRIMARY).start(
        request.model_copy(update={"device_serial": PRIMARY})
    )


@router.post(
    "/task/stop",
    response_model=RFStatus,
)
def rf_stop() -> RFStatus:
    return get_dual_rf_controller()._get(PRIMARY).stop()



# JARVIS_ADSB_R5_ROUTES
from core.rf.adsb import adsb_stats, aircraft_snapshot


@router.get("/adsb/aircraft")
def rf_adsb_aircraft():
    """Return normalized live ADS-B aircraft tracks."""
    return aircraft_snapshot()


@router.get("/adsb/stats")
def rf_adsb_stats():
    """Return normalized ADS-B receiver statistics."""
    return adsb_stats()


# JARVIS_DUAL_RF_R1_ROUTES
@router.get("/receivers")
def rf_receivers():
    return get_dual_rf_controller().status()

@router.get("/receivers/{serial}/status")
def rf_receiver_status(serial: str):
    try:
        return get_dual_rf_controller().status(serial)
    except (ValueError, KeyError):
        raise HTTPException(status_code=404, detail="Unknown SDR receiver")

@router.post("/receivers/{serial}/start")
def rf_receiver_start(serial: str, request: RFTaskRequest):
    try:
        return get_dual_rf_controller().start(serial, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/receivers/{serial}/stop")
def rf_receiver_stop(serial: str):
    try:
        return get_dual_rf_controller().stop(serial)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
