"""GPS adapter using the local gpsd JSON protocol."""

from __future__ import annotations

import json
import socket
import time
from typing import Any

from .models import GPSStatus


GPSD_HOST = "127.0.0.1"
GPSD_PORT = 2947


def _normalize_gps_messages(messages: list[dict[str, Any]]) -> GPSStatus:
    devices: list[dict[str, Any]] = []
    best_tpv: dict[str, Any] | None = None

    for message in messages:
        message_class = message.get("class")

        if message_class == "DEVICES":
            raw_devices = message.get("devices")
            if isinstance(raw_devices, list):
                devices = [
                    item
                    for item in raw_devices
                    if isinstance(item, dict)
                ]

        elif message_class == "TPV":
            if best_tpv is None:
                best_tpv = message
            else:
                current_mode = int(message.get("mode") or 0)
                best_mode = int(best_tpv.get("mode") or 0)
                if current_mode >= best_mode:
                    best_tpv = message

    device_name = None

    if best_tpv:
        device_name = best_tpv.get("device")

    if not device_name and devices:
        device_name = devices[0].get("path")

    if not devices and best_tpv is None:
        return GPSStatus(
            state="no_device",
            available=False,
            fix=False,
            detail="gpsd is reachable but no GPS device is reporting data.",
        )

    if best_tpv is None:
        return GPSStatus(
            state="no_fix",
            available=True,
            fix=False,
            device=device_name,
            detail="GPS device is visible to gpsd but no TPV fix is available.",
        )

    mode = int(best_tpv.get("mode") or 0)

    lat = best_tpv.get("lat")
    lon = best_tpv.get("lon")

    has_fix = (
        mode >= 2
        and isinstance(lat, (int, float))
        and isinstance(lon, (int, float))
    )

    if not has_fix:
        return GPSStatus(
            state="no_fix",
            available=True,
            fix=False,
            mode=mode,
            device=device_name,
            timestamp=best_tpv.get("time"),
            detail="GPS is connected but does not currently have a position fix.",
        )

    altitude = best_tpv.get("altMSL")
    if altitude is None:
        altitude = best_tpv.get("alt")

    return GPSStatus(
        state="fix",
        available=True,
        fix=True,
        mode=mode,
        latitude=float(lat),
        longitude=float(lon),
        altitude_m=float(altitude) if isinstance(altitude, (int, float)) else None,
        speed_mps=(
            float(best_tpv["speed"])
            if isinstance(best_tpv.get("speed"), (int, float))
            else None
        ),
        track_deg=(
            float(best_tpv["track"])
            if isinstance(best_tpv.get("track"), (int, float))
            else None
        ),
        timestamp=best_tpv.get("time"),
        device=device_name,
        detail="Valid GPS position fix.",
    )


def gps_status(
    host: str = GPSD_HOST,
    port: int = GPSD_PORT,
    observation_seconds: float = 1.25,
) -> GPSStatus:
    messages: list[dict[str, Any]] = []

    try:
        with socket.create_connection(
            (host, port),
            timeout=1.0,
        ) as sock:
            sock.settimeout(0.25)

            command = (
                '?WATCH={"enable":true,"json":true};\n'
                "?POLL;\n"
            )
            sock.sendall(command.encode("ascii"))

            deadline = time.monotonic() + observation_seconds
            buffer = b""

            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(8192)
                except socket.timeout:
                    continue

                if not chunk:
                    break

                buffer += chunk

                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    raw = raw.strip()

                    if not raw:
                        continue

                    try:
                        decoded = json.loads(
                            raw.decode("utf-8", errors="replace")
                        )
                    except json.JSONDecodeError:
                        continue

                    if isinstance(decoded, dict):
                        messages.append(decoded)

    except (ConnectionRefusedError, TimeoutError, socket.timeout):
        return GPSStatus(
            state="gpsd_unavailable",
            available=False,
            fix=False,
            detail="gpsd is not reachable on localhost:2947.",
        )
    except OSError as exc:
        return GPSStatus(
            state="error",
            available=False,
            fix=False,
            detail=f"GPS query failed: {exc}",
        )

    return _normalize_gps_messages(messages)
