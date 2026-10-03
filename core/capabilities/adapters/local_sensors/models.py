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


class MobileSensorStatus(BaseModel):
    state: Literal[
        "online",
        "stale",
        "no_data",
        "error",
    ]
    available: bool = False

    node_id: str | None = None

    # Node / transport freshness.
    received_at: str | None = None
    age_seconds: float | None = None

    # Actual GNSS observation freshness.
    observed_at: str | None = None
    fix_age_seconds: float | None = None
    fix_stale: bool = False

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    horizontal_accuracy_m: float | None = None

    heading_deg: float | None = None
    speed_mps: float | None = None

    capabilities: list[str] = []

    detail: str | None = None


class ObserverStatus(BaseModel):
    state: Literal[
        "fix",
        "unavailable",
    ]

    available: bool = False

    source: Literal[
        "gpsd",
        "mobile_gnss",
    ] | None = None

    node_id: str | None = None

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None

    heading_deg: float | None = None
    speed_mps: float | None = None

    horizontal_accuracy_m: float | None = None

    timestamp: str | None = None
    age_seconds: float | None = None

    detail: str | None = None


class SensorSnapshot(BaseModel):
    schema: str = "jarvis.local_sensors.r1"
    host: str

    sdr: SDRStatus
    gps: GPSStatus
    mobile: MobileSensorStatus
    observer: ObserverStatus
