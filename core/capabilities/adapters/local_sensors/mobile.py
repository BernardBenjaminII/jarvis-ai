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

from .models import (
    MobileSensorChannelStatus,
    MobileSensorStatus,
)


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

_CHANNEL_STALE_SECONDS: dict[str, float] = {
    "gnss": _GNSS_STALE_SECONDS,
    "compass": float(
        os.getenv("JARVIS_MOBILE_COMPASS_STALE_SECONDS", "180")
    ),
    "accelerometer": float(
        os.getenv("JARVIS_MOBILE_IMU_STALE_SECONDS", "5")
    ),
    "gyroscope": float(
        os.getenv("JARVIS_MOBILE_IMU_STALE_SECONDS", "5")
    ),
    "magnetometer": float(
        os.getenv("JARVIS_MOBILE_IMU_STALE_SECONDS", "5")
    ),
    "device_motion": float(
        os.getenv("JARVIS_MOBILE_IMU_STALE_SECONDS", "5")
    ),
    "barometer": float(
        os.getenv("JARVIS_MOBILE_BAROMETER_STALE_SECONDS", "10")
    ),
    "relative_altitude": float(
        os.getenv("JARVIS_MOBILE_BAROMETER_STALE_SECONDS", "10")
    ),
    "absolute_altitude": float(
        os.getenv(
            "JARVIS_MOBILE_ABSOLUTE_ALTITUDE_STALE_SECONDS",
            "30",
        )
    ),
    "activity": float(
        os.getenv("JARVIS_MOBILE_ACTIVITY_STALE_SECONDS", "300")
    ),
    "pedometer": float(
        os.getenv("JARVIS_MOBILE_PEDOMETER_STALE_SECONDS", "300")
    ),
    "battery": float(
        os.getenv("JARVIS_MOBILE_DEVICE_STALE_SECONDS", "15")
    ),
    "thermal": float(
        os.getenv("JARVIS_MOBILE_DEVICE_STALE_SECONDS", "15")
    ),
    "proximity": float(
        os.getenv("JARVIS_MOBILE_DEVICE_STALE_SECONDS", "15")
    ),
}

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


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _append_unique(result: list[str], value: str) -> None:
    if value not in result:
        result.append(value)


def _capabilities(
    packet: dict[str, Any],
) -> list[str]:
    """Return R3 capabilities plus legacy Jarvis aliases."""

    result: list[str] = []

    advertised = packet.get("capabilities")

    if isinstance(advertised, list):
        for item in advertised:
            if isinstance(item, str) and item.strip():
                _append_unique(result, item.strip())

    location = _dict(packet.get("location"))
    heading = _dict(packet.get("heading"))
    motion = _dict(packet.get("motion"))
    raw = _dict(packet.get("raw"))
    environment = _dict(packet.get("environment"))
    legacy_barometer = _dict(packet.get("barometer"))
    activity = _dict(packet.get("activity"))
    pedometer = _dict(packet.get("pedometer"))
    device = _dict(packet.get("device"))

    if location:
        _append_unique(result, "gnss")

    if heading:
        _append_unique(result, "compass")
        _append_unique(result, "heading")

    if motion:
        _append_unique(result, "device_motion")
        _append_unique(result, "imu")

    if _dict(raw.get("accelerometer")):
        _append_unique(result, "accelerometer")

    if _dict(raw.get("gyroscope")):
        _append_unique(result, "gyroscope")

    if _dict(raw.get("magnetometer")):
        _append_unique(result, "magnetometer")

    if (
        "pressure_kpa" in environment
        or "barometer_observed_at" in environment
        or legacy_barometer
    ):
        _append_unique(result, "barometer")

    if "relative_altitude_m" in environment:
        _append_unique(result, "relative_altitude")

    if "absolute_altitude_m" in environment:
        _append_unique(result, "absolute_altitude")

    if activity:
        _append_unique(result, "activity")

    if pedometer:
        _append_unique(result, "pedometer")

    if (
        "battery_level" in device
        or "battery_percent" in device
        or "battery_state" in device
    ):
        _append_unique(result, "battery")

    if "thermal_state" in device:
        _append_unique(result, "thermal")

    if "proximity_near" in device:
        _append_unique(result, "proximity")

    return result


def _channel(
    *,
    observed_at: Any,
    stale_after_seconds: float,
    present: bool,
) -> MobileSensorChannelStatus:
    if not present:
        return MobileSensorChannelStatus(
            state="no_data",
            available=False,
            stale_after_seconds=stale_after_seconds,
            detail="No telemetry has been observed for this channel.",
        )

    timestamp, age_seconds = _timestamp_age_seconds(observed_at)

    if timestamp is None or age_seconds is None:
        return MobileSensorChannelStatus(
            state="no_data",
            available=True,
            observed_at=timestamp,
            stale_after_seconds=stale_after_seconds,
            detail=(
                "Channel exists but no valid observation timestamp "
                "is available."
            ),
        )

    if age_seconds > stale_after_seconds:
        return MobileSensorChannelStatus(
            state="stale",
            available=True,
            observed_at=timestamp,
            age_seconds=round(age_seconds, 3),
            stale_after_seconds=stale_after_seconds,
            detail=f"Last observation is {age_seconds:.1f}s old.",
        )

    return MobileSensorChannelStatus(
        state="live",
        available=True,
        observed_at=timestamp,
        age_seconds=round(age_seconds, 3),
        stale_after_seconds=stale_after_seconds,
        detail="Channel telemetry is current.",
    )


def _event_channel(
    *,
    observed_at: Any,
    heartbeat_at: Any,
    present: bool,
    name: str,
) -> MobileSensorChannelStatus:
    # Event-driven freshness:
    # activity and pedometer timestamps represent the last event/state
    # transition, not a continuously sampled measurement.

    if not present:
        return MobileSensorChannelStatus(
            state="no_data",
            available=False,
            detail=f"No telemetry has been observed for {name}.",
        )

    event_timestamp, event_age = _timestamp_age_seconds(
        observed_at
    )

    _, heartbeat_age = _timestamp_age_seconds(
        heartbeat_at
    )

    if heartbeat_age is None:
        return MobileSensorChannelStatus(
            state="no_data",
            available=True,
            observed_at=event_timestamp,
            age_seconds=(
                round(event_age, 3)
                if event_age is not None
                else None
            ),
            detail=(
                f"{name} data exists but Jarvis cannot establish "
                "a current sensor-node heartbeat."
            ),
        )

    if heartbeat_age > _STALE_SECONDS:
        return MobileSensorChannelStatus(
            state="stale",
            available=True,
            observed_at=event_timestamp,
            age_seconds=(
                round(event_age, 3)
                if event_age is not None
                else None
            ),
            stale_after_seconds=_STALE_SECONDS,
            detail=(
                f"{name} is event-driven; the sensor-node heartbeat "
                f"is stale ({heartbeat_age:.1f}s old)."
            ),
        )

    if event_age is None:
        detail = (
            f"{name} is available and the sensor-node heartbeat "
            "is current; no event timestamp is available."
        )
    else:
        detail = (
            f"{name} is event-driven and available; sensor-node "
            f"heartbeat is current. Last event was {event_age:.1f}s ago."
        )

    return MobileSensorChannelStatus(
        state="live",
        available=True,
        observed_at=event_timestamp,
        age_seconds=(
            round(event_age, 3)
            if event_age is not None
            else None
        ),
        stale_after_seconds=None,
        detail=detail,
    )


def _sensor_channels(
    packet: dict[str, Any],
) -> dict[str, MobileSensorChannelStatus]:
    """Build independent freshness for each R3 sensor family."""

    raw_advertised = packet.get("capabilities")
    advertised = {
        item
        for item in raw_advertised
        if isinstance(item, str)
    } if isinstance(raw_advertised, list) else set()

    location = _dict(packet.get("location"))
    heading = _dict(packet.get("heading"))
    motion = _dict(packet.get("motion"))
    raw = _dict(packet.get("raw"))
    accelerometer = _dict(raw.get("accelerometer"))
    gyroscope = _dict(raw.get("gyroscope"))
    magnetometer = _dict(raw.get("magnetometer"))
    environment = _dict(packet.get("environment"))
    legacy_barometer = _dict(packet.get("barometer"))
    activity = _dict(packet.get("activity"))
    pedometer = _dict(packet.get("pedometer"))
    device = _dict(packet.get("device"))

    def expected(name: str, data: dict[str, Any]) -> bool:
        return bool(data) or name in advertised

    return {
        "gnss": _channel(
            observed_at=packet.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["gnss"],
            present=expected("gnss", location),
        ),
        "compass": _channel(
            observed_at=heading.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["compass"],
            present=expected("compass", heading),
        ),
        "accelerometer": _channel(
            observed_at=accelerometer.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["accelerometer"],
            present=expected("accelerometer", accelerometer),
        ),
        "gyroscope": _channel(
            observed_at=gyroscope.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["gyroscope"],
            present=expected("gyroscope", gyroscope),
        ),
        "magnetometer": _channel(
            observed_at=magnetometer.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["magnetometer"],
            present=expected("magnetometer", magnetometer),
        ),
        "device_motion": _channel(
            observed_at=motion.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["device_motion"],
            present=expected("device_motion", motion),
        ),
        "barometer": _channel(
            observed_at=(
                environment.get("barometer_observed_at")
                or legacy_barometer.get("observed_at")
            ),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["barometer"],
            present=(
                "barometer" in advertised
                or "pressure_kpa" in environment
                or bool(legacy_barometer)
            ),
        ),
        "relative_altitude": _channel(
            observed_at=environment.get("barometer_observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["relative_altitude"],
            present=(
                "relative_altitude" in advertised
                or "relative_altitude_m" in environment
            ),
        ),
        "absolute_altitude": _channel(
            observed_at=environment.get("absolute_altitude_observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["absolute_altitude"],
            present=(
                "absolute_altitude" in advertised
                or "absolute_altitude_m" in environment
            ),
        ),
        "activity": _event_channel(
            observed_at=activity.get("observed_at"),
            heartbeat_at=device.get("observed_at"),
            present=expected("activity", activity),
            name="Activity recognition",
        ),
        "pedometer": _event_channel(
            observed_at=pedometer.get("observed_at"),
            heartbeat_at=device.get("observed_at"),
            present=expected("pedometer", pedometer),
            name="Pedometer",
        ),
        "battery": _channel(
            observed_at=device.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["battery"],
            present=(
                "battery" in advertised
                or "battery_level" in device
                or "battery_percent" in device
                or "battery_state" in device
            ),
        ),
        "thermal": _channel(
            observed_at=device.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["thermal"],
            present=(
                "thermal" in advertised
                or "thermal_state" in device
            ),
        ),
        "proximity": _channel(
            observed_at=device.get("observed_at"),
            stale_after_seconds=_CHANNEL_STALE_SECONDS["proximity"],
            present=(
                "proximity" in advertised
                or "proximity_near" in device
            ),
        ),
    }


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

    received_at, age_seconds = _packet_age_seconds(packet)
    observed_at, fix_age_seconds = _fix_age_seconds(packet)

    location = _dict(packet.get("location"))
    heading = _dict(packet.get("heading"))

    latitude = _number(location.get("latitude"))
    longitude = _number(location.get("longitude"))
    altitude = _number(location.get("altitude_m"))
    accuracy = _number(location.get("horizontal_accuracy_m"))
    speed = _number(location.get("speed_mps"))

    true_heading = _number(heading.get("true_deg"))
    magnetic_heading = _number(heading.get("magnetic_deg"))

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

    channels = _sensor_channels(packet)

    live_channels = [
        name
        for name, channel in channels.items()
        if channel.state == "live"
    ]

    stale_channels = [
        name
        for name, channel in channels.items()
        if channel.state == "stale"
    ]

    no_data_channels = [
        name
        for name, channel in channels.items()
        if channel.state == "no_data"
    ]

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
        channels=channels,
        live_channels=live_channels,
        stale_channels=stale_channels,
        no_data_channels=no_data_channels,
        detail=detail,
    )
