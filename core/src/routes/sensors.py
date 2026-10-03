"""Local physical sensor API."""

from __future__ import annotations

import os
from typing import Any

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from core.capabilities.adapters.local_sensors import (
    sensor_snapshot,
)

from core.capabilities.adapters.local_sensors.mobile import (
    MobileTelemetryError,
    ingest_mobile_telemetry,
    latest_mobile_telemetry,
    mobile_status,
)

from core.capabilities.adapters.local_sensors.gps import (
    gps_status,
)

from core.capabilities.adapters.local_sensors.observer import (
    observer_status,
)

from core.capabilities.adapters.local_sensors.models import (
    MobileSensorStatus,
    ObserverStatus,
    SensorSnapshot,
)


router = APIRouter(
    prefix="/api/sensors",
    tags=["Local Sensors"],
)


def _expected_mobile_token() -> str:
    return os.getenv(
        "JARVIS_MOBILE_SENSOR_TOKEN",
        "jarvis-dev-sensor",
    )


def _verify_mobile_token(
    supplied: str | None,
) -> None:
    if supplied != _expected_mobile_token():
        raise HTTPException(
            status_code=401,
            detail="Invalid mobile sensor token.",
        )


@router.get(
    "/status",
    response_model=SensorSnapshot,
)
def local_sensor_status() -> SensorSnapshot:
    """
    Return normalized state for local physical sensors.

    Sources currently include:
      - RTL-SDR hardware
      - gpsd-connected GNSS receivers
      - mobile sensor nodes

    Device absence is represented as sensor state rather than
    an API failure.
    """
    return sensor_snapshot()



@router.get(
    "/observer",
    response_model=ObserverStatus,
)
def current_observer_status() -> ObserverStatus:
    """
    Return Jarvis' authoritative live observer position.

    R1 source priority:
      1. gpsd GNSS
      2. mobile GNSS

    Stale mobile telemetry is never promoted to a live fix.
    """

    gps = gps_status()
    mobile = mobile_status()

    return observer_status(
        gps=gps,
        mobile=mobile,
    )



@router.get(
    "/mobile/status",
    response_model=MobileSensorStatus,
)
def mobile_sensor_status() -> MobileSensorStatus:
    """Return normalized mobile sensor health/state."""
    return mobile_status()


@router.get("/mobile/latest")
def mobile_sensor_latest() -> dict[str, Any]:
    """Return the latest accepted mobile telemetry packet."""

    packet = latest_mobile_telemetry()

    if packet is None:
        raise HTTPException(
            status_code=404,
            detail="No mobile telemetry received.",
        )

    return packet


@router.post("/mobile/telemetry")
def mobile_sensor_telemetry(
    payload: dict[str, Any],
    x_jarvis_token: str | None = Header(
        default=None,
        alias="X-Jarvis-Token",
    ),
) -> dict[str, Any]:
    """Accept telemetry from an authorized mobile sensor node."""

    _verify_mobile_token(
        x_jarvis_token
    )

    try:
        return ingest_mobile_telemetry(
            payload
        )

    except MobileTelemetryError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
