"""Jarvis mobile sensor adapter.

Accepts telemetry from mobile sensor nodes and exposes normalized
health/location state to the local-sensor service.

The transport is intentionally independent from the mobile platform.
An iPhone, Android device, or future embedded sensor can send the same
telemetry contract.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import MobileSensorStatus


_STATE_DIR = Path(
    os.getenv(
        "JARVIS_MOBILE_SENSOR_STATE_DIR",
        "/tmp/jarvis_mobile_sensor",
    )
)

_LATEST = _STATE_DIR / "latest.json"

_STALE_SECONDS = float(
    os.getenv(
        "JARVIS_MOBILE_SENSOR_STALE_SECONDS",
        "15",
    )
)

_GNSS_STALE_SECONDS = float(
    os.getenv(
        "JARVIS_MOBILE_GNSS_STALE_SECONDS",
        "30",
    )
)

_LOCK = threading.Lock()


class MobileTelemetryError(ValueError):
    """Invalid mobile telemetry packet."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    return None


def _read_latest() -> dict[str, Any] | None:
    with _LOCK:
        if not _LATEST.exists():
            return None

        try:
            data = json.loads(
                _LATEST.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return None

    return data if isinstance(data, dict) else None


def latest_mobile_telemetry() -> dict[str, Any] | None:
    """Return the most recently accepted mobile telemetry packet."""
    return _read_latest()


def ingest_mobile_telemetry(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate and persist a mobile sensor packet."""

    if not isinstance(payload, dict):
        raise MobileTelemetryError(
            "Telemetry payload must be a JSON object."
        )

    node_id = payload.get("node_id")

    if not isinstance(node_id, str) or not node_id.strip():
        raise MobileTelemetryError(
            "Telemetry requires a non-empty node_id."
        )

    packet = dict(payload)

    packet["_jarvis"] = {
        "received_at": _iso_now(),
        "source": "mobile_sensor",
    }

    _STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    encoded = json.dumps(
        packet,
        indent=2,
        sort_keys=True,
    )

    tmp = _LATEST.with_suffix(".json.tmp")

    with _LOCK:
        tmp.write_text(
            encoded,
            encoding="utf-8",
        )
        os.replace(tmp, _LATEST)

    return {
        "accepted": True,
        "node_id": node_id,
        "received_at": packet["_jarvis"]["received_at"],
    }


def _timestamp_age_seconds(
    timestamp: Any,
) -> tuple[str | None, float | None]:
    """Return normalized age for an ISO-8601 timestamp."""

    if not isinstance(timestamp, str):
        return None, None

    try:
        value = timestamp.replace(
            "Z",
            "+00:00",
        )

        observed = datetime.fromisoformat(value)

        if observed.tzinfo is None:
            observed = observed.replace(
                tzinfo=timezone.utc
            )

        age = (
            _utc_now()
            - observed.astimezone(timezone.utc)
        ).total_seconds()

        return timestamp, max(0.0, age)

    except ValueError:
        return timestamp, None


def _packet_age_seconds(
    packet: dict[str, Any],
) -> tuple[str | None, float | None]:
    """Return node/transport age from Jarvis receive time."""

    jarvis_meta = packet.get("_jarvis")

    if not isinstance(jarvis_meta, dict):
        return None, None

    return _timestamp_age_seconds(
        jarvis_meta.get("received_at")
    )


def _fix_age_seconds(
    packet: dict[str, Any],
) -> tuple[str | None, float | None]:
    """Return age of the actual mobile GNSS observation."""

    return _timestamp_age_seconds(
        packet.get("observed_at")
    )


def _capabilities(
    packet: dict[str, Any],
) -> list[str]:
    result: list[str] = []

    mappings = (
        ("location", "gnss"),
        ("heading", "heading"),
        ("motion", "imu"),
        ("accelerometer", "accelerometer"),
        ("gyroscope", "gyroscope"),
        ("magnetometer", "magnetometer"),
        ("barometer", "barometer"),
    )

    for packet_key, capability in mappings:
        if isinstance(
            packet.get(packet_key),
            dict,
        ):
            result.append(capability)

    device = packet.get("device")

    if isinstance(device, dict):
        if (
            "battery_percent" in device
            or "battery_state" in device
        ):
            result.append("battery")

    return result


def mobile_status() -> MobileSensorStatus:
    """Return normalized health and geospatial state."""

    packet = _read_latest()

    if packet is None:
        return MobileSensorStatus(
            state="no_data",
            available=False,
            detail=(
                "No mobile sensor telemetry "
                "has been received."
            ),
        )

    node_id = packet.get("node_id")

    if not isinstance(node_id, str):
        node_id = None

    received_at, age_seconds = (
        _packet_age_seconds(packet)
    )

    observed_at, fix_age_seconds = (
        _fix_age_seconds(packet)
    )

    location = packet.get("location")

    if not isinstance(location, dict):
        location = {}

    heading = packet.get("heading")

    if not isinstance(heading, dict):
        heading = {}

    latitude = _number(
        location.get("latitude")
    )

    longitude = _number(
        location.get("longitude")
    )

    altitude = _number(
        location.get("altitude_m")
    )

    accuracy = _number(
        location.get(
            "horizontal_accuracy_m"
        )
    )

    speed = _number(
        location.get("speed_mps")
    )

    true_heading = _number(
        heading.get("true_deg")
    )

    magnetic_heading = _number(
        heading.get("magnetic_deg")
    )

    heading_deg = (
        true_heading
        if true_heading is not None
        and true_heading >= 0
        else magnetic_heading
    )

    has_coordinates = (
        latitude is not None
        and longitude is not None
    )

    if not has_coordinates:
        fix_stale = False

    elif fix_age_seconds is None:
        # Coordinates exist, but Jarvis cannot establish when
        # they were actually observed. Do not promote them as
        # a live GNSS fix.
        fix_stale = True

    else:
        fix_stale = (
            fix_age_seconds > _GNSS_STALE_SECONDS
        )

    if age_seconds is None:
        state = "error"
        available = False
        detail = (
            "Mobile telemetry exists but "
            "its receive timestamp is invalid."
        )

    elif age_seconds > _STALE_SECONDS:
        state = "stale"
        available = True
        detail = (
            f"Mobile telemetry is stale "
            f"({age_seconds:.1f}s old)."
        )

    else:
        state = "online"
        available = True
        detail = "Mobile sensor telemetry is current."

    return MobileSensorStatus(
        state=state,
        available=available,
        node_id=node_id,
        received_at=received_at,
        age_seconds=(
            round(age_seconds, 3)
            if age_seconds is not None
            else None
        ),
        observed_at=observed_at,
        fix_age_seconds=(
            round(fix_age_seconds, 3)
            if fix_age_seconds is not None
            else None
        ),
        fix_stale=fix_stale,
        latitude=latitude,
        longitude=longitude,
        altitude_m=altitude,
        horizontal_accuracy_m=accuracy,
        heading_deg=heading_deg,
        speed_mps=speed,
        capabilities=_capabilities(packet),
        detail=detail,
    )
