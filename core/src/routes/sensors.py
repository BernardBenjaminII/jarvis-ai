"""Local physical sensor API."""

from __future__ import annotations

from fastapi import APIRouter

from core.capabilities.adapters.local_sensors import sensor_snapshot
from core.capabilities.adapters.local_sensors.models import SensorSnapshot


router = APIRouter(
    prefix="/api/sensors",
    tags=["Local Sensors"],
)


@router.get("/status", response_model=SensorSnapshot)
def local_sensor_status() -> SensorSnapshot:
    """
    Return normalized health and observation state for local sensors.

    R1 exposes:
      - RTL-SDR hardware discovery/readiness
      - GPS state through the local gpsd service

    GPS absence or lack of satellite fix is represented as sensor state
    rather than an API failure.
    """
    return sensor_snapshot()
