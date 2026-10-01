"""Normalized local-sensor models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SDRStatus(BaseModel):
    state: Literal[
        "ready",
        "unavailable",
        "permission_denied",
        "busy",
        "error",
    ]
    available: bool = False
    manufacturer: str | None = None
    product: str | None = None
    serial: str | None = None
    tuner: str | None = None
    sample_rate: int | None = None
    detail: str | None = None


class GPSStatus(BaseModel):
    state: Literal[
        "fix",
        "no_fix",
        "no_device",
        "gpsd_unavailable",
        "error",
    ]
    available: bool = False
    fix: bool = False
    mode: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    speed_mps: float | None = None
    track_deg: float | None = None
    timestamp: str | None = None
    device: str | None = None
    detail: str | None = None


class SensorSnapshot(BaseModel):
    schema: str = "jarvis.local_sensors.r1"
    host: str
    sdr: SDRStatus
    gps: GPSStatus
