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


# JARVIS_WIFI_R1A_ROUTES
import subprocess
from hmac import compare_digest as _wifi_compare_digest
from core.capabilities.adapters.local_sensors.wifi import inventory as _wifi_inventory, capture as _wifi_capture

@router.get('/wifi/status')
def wifi_sensor_status():
    return _wifi_inventory()

@router.post('/wifi/{sensor_id}/capture')
def wifi_sensor_capture(sensor_id: str, seconds: int = 10,
                        x_jarvis_wifi_token: str | None = Header(default=None, alias='X-Jarvis-WiFi-Token')):
    expected = os.environ.get('JARVIS_WIFI_SENSOR_TOKEN', '')
    if not expected or not x_jarvis_wifi_token or not _wifi_compare_digest(x_jarvis_wifi_token, expected):
        raise HTTPException(status_code=401, detail='Wi-Fi sensor capture authorization required')
    try:
        return _wifi_capture(sensor_id, seconds)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


# JARVIS_WIFI_R29B_AP_INVENTORY
import sqlite3 as _wifi_sqlite3
from pathlib import Path as _WiFiPath

_WIFI_AP_DB = (
    _WiFiPath.home()
    / ".local/state/jarvis/wifi_ap.sqlite3"
)

@router.get("/wifi/networks")
def wifi_networks():
    if not _WIFI_AP_DB.is_file():
        return {
            "sensor_id": "WIFI",
            "networks": [],
            "available": False,
        }

    with _wifi_sqlite3.connect(
        f"file:{_WIFI_AP_DB}?mode=ro",
        uri=True,
        timeout=2,
    ) as db:
        db.row_factory = _wifi_sqlite3.Row
        rows = db.execute("""
            SELECT sensor_id, bssid,
                   ssid_hex, ssid_display,
                   channel_ie, signal_dbm,
                   security, akms_json,
                   first_seen, last_seen,
                   frames_seen
            FROM access_points
            ORDER BY last_seen DESC, frames_seen DESC
            LIMIT 500
        """).fetchall()

        return {
            "sensor_id": "WIFI",
            "available": True,
            "networks": [dict(row) for row in rows],
        }


# JARVIS_IOT_R2_2_ROUTES
from core.src.routes.iot_sensor import router as iot_router
router.include_router(iot_router)


# JARVIS_WIFI_R210C_SIGNAL_API
@router.get("/wifi/signal-history")
def wifi_signal_history(
    sensor_id: str,
    bssid: str,
    hours: int = 24,
):
    """Read-only historical Wi-Fi RSSI measurements."""
    import re
    import math
    from datetime import datetime, timezone, timedelta
    from fastapi import HTTPException

    if sensor_id not in ("WIFI-01", "WIFI-02"):
        raise HTTPException(status_code=400, detail="Invalid sensor")

    bssid = bssid.lower()
    if not re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", bssid):
        raise HTTPException(status_code=400, detail="Invalid BSSID")

    if hours not in (24, 168, 720, 2160):
        raise HTTPException(status_code=400, detail="Unsupported period")

    cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=hours)
    ).isoformat()

    if not _WIFI_AP_DB.is_file():
        raise HTTPException(status_code=503, detail="Inventory unavailable")

    with _wifi_sqlite3.connect(
        f"file:{_WIFI_AP_DB}?mode=ro",
        uri=True,
        timeout=3,
    ) as db:
        exists = db.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type='table' AND name='wifi_signal_history'
        """).fetchone()

        if not exists:
            raise HTTPException(
                status_code=503,
                detail="Signal history unavailable"
            )

        total = db.execute("""
            SELECT COUNT(*)
            FROM wifi_signal_history
            WHERE sensor_id = ?
              AND bssid = ?
              AND observed_at >= ?
        """, (sensor_id, bssid, cutoff)).fetchone()[0]

        # Bound response size while retaining chronological
        # coverage of the requested period.
        stride = max(1, math.ceil(total / 1500))

        rows = db.execute("""
            SELECT observed_at, signal_dbm,
                   channel, frames_observed
            FROM (
                SELECT observed_at, signal_dbm,
                       channel, frames_observed,
                       ROW_NUMBER() OVER (
                           ORDER BY observed_at
                       ) AS rn
                FROM wifi_signal_history
                WHERE sensor_id = ?
                  AND bssid = ?
                  AND observed_at >= ?
            )
            WHERE (rn - 1) % ? = 0
            ORDER BY observed_at
        """, (sensor_id, bssid, cutoff, stride)).fetchall()

    return {
        "schema": "jarvis.wifi.signal.r210c",
        "sensor_id": sensor_id,
        "bssid": bssid,
        "hours": hours,
        "retention_days": 90,
        "total_samples": total,
        "returned_samples": len(rows),
        "samples": [
            {
                "timestamp": timestamp,
                "rssi_dbm": rssi,
                "channel": channel,
                "frames": frames,
            }
            for timestamp, rssi, channel, frames in rows
        ],
    }



# JARVIS_WIFI_R211A_TOPOLOGY
@router.get("/wifi/topology")
def wifi_local_topology():
    """Read-only association, gateway, and LAN neighbor evidence."""
    import json
    import re
    import socket
    import subprocess
    from datetime import datetime, timezone

    interface = "wlp5s0"

    def run_command(*args):
        try:
            result = subprocess.run(
                list(args),
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            return result.stdout if result.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""

    link = run_command("iw", "dev", interface, "link")

    addresses = run_command(
        "ip", "-j", "-4", "addr", "show",
        "dev", interface
    )

    routes = run_command(
        "ip", "-j", "-4", "route", "show",
        "default"
    )

    neighbors = run_command(
        "ip", "-j", "-4", "neigh", "show",
        "dev", interface
    )

    def parse_json(raw):
        try:
            return json.loads(raw) if raw else []
        except (ValueError, TypeError):
            return []

    bssid_match = re.search(
        r"Connected to ([0-9a-f:]{17})",
        link,
        re.IGNORECASE
    )

    # R2.11A.1: Parse the SSID from iw link output.
    # Preserve the actual name, including spaces.
    bssid = (
        bssid_match.group(1).lower()
        if bssid_match else None
    )

    ssid = next(
        (
            line.split("SSID:", 1)[1].strip()
            for line in link.splitlines()
            if line.strip().startswith("SSID:")
        ),
        None
    )

    address_data = parse_json(addresses)
    route_data = parse_json(routes)
    neighbor_data = parse_json(neighbors)

    local_ip = None

    for item in address_data:
        for info in item.get("addr_info", []):
            if info.get("family") == "inet":
                local_ip = info.get("local")
                break

    gateway = next(
        (
            r.get("gateway")
            for r in route_data
            if r.get("dev") == interface
            and r.get("gateway")
        ),
        None
    )

    peers = []

    for entry in neighbor_data:
        ip = entry.get("dst")
        mac = entry.get("lladdr")

        if not ip or not mac:
            continue

        peers.append({
            "ip": ip,
            "mac": mac.lower(),
            "state": entry.get("state", []),
            "role": (
                "gateway" if ip == gateway
                else "lan_peer"
            ),
            "connection_type": "unknown",
        })

    return {
        "schema": "jarvis.wifi.topology.r211a",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "interface": interface,
        "host_ip": local_ip,
        "association": {
            "ssid": ssid,
            "bssid": bssid,
        },
        "gateway_ip": gateway,
        "neighbors": peers,
        "evidence": {
            "association": "iw link",
            "gateway": "kernel routing table",
            "neighbors": "kernel neighbor cache",
            "note": (
                "Neighbor entries do not prove Wi-Fi association "
                "or physical device location."
            ),
        },
    }


# JARVIS_R212A_LAN_IDENTITIES
@router.get("/wifi/lan-identities")
def wifi_lan_identities():
    """Read-only, locally discovered LAN device identities."""
    import json
    import sqlite3
    from pathlib import Path

    database = (
        Path.home() /
        ".local/state/jarvis/lan_identity.sqlite3"
    )

    if not database.is_file():
        return {
            "schema": "jarvis.lan.identity.r212a",
            "devices": [],
            "status": "collector_not_initialized",
        }

    connection = sqlite3.connect(
        database.as_uri() + "?mode=ro",
        uri=True,
        timeout=2,
    )
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute("""
            SELECT device_key, ip, mac, hostname,
                   display_name, device_type,
                   identity_source, services_json,
                   neighbor_state_json,
                   first_seen, last_seen
            FROM lan_devices
            WHERE ip NOT LIKE '127.%'
            ORDER BY ip
        """).fetchall()
    finally:
        connection.close()

    devices = []
    for row in rows:
        device = dict(row)
        device["services"] = json.loads(
            device.pop("services_json") or "[]"
        )
        device["neighbor_state"] = json.loads(
            device.pop("neighbor_state_json") or "[]"
        )
        devices.append(device)

    return {
        "schema": "jarvis.lan.identity.r212a",
        "status": "ok",
        "devices": devices,
    }
