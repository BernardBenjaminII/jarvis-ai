"""JARVIS IOT-01 read-only BLE sensor API."""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/iot", tags=["IoT Sensors"])

DB_PATH = Path(
    os.getenv(
        "JARVIS_IOT01_DB",
        str(Path.home() / ".local/state/jarvis/iot01.sqlite3"),
    )
)

STALE_SECONDS = 30


def connect():
    if not DB_PATH.is_file():
        return None

    try:
        db = sqlite3.connect(
            f"file:{DB_PATH}?mode=ro",
            uri=True,
            timeout=2,
        )
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error:
        return None


@router.get("/status")
def status():
    db = connect()

    if db is None:
        return {
            "sensor_id": "IOT-01",
            "state": "no_data",
            "available": False,
        }

    try:
        row = db.execute("""
            SELECT last_heartbeat, firmware, uptime_ms
            FROM health
            WHERE sensor_id = 'IOT-01'
        """).fetchone()
    finally:
        db.close()

    if row is None:
        return {
            "sensor_id": "IOT-01",
            "state": "no_data",
            "available": False,
        }

    received = datetime.fromisoformat(row["last_heartbeat"])
    age = max(
        0,
        (datetime.now(timezone.utc) - received).total_seconds(),
    )
    online = age <= STALE_SECONDS

    return {
        "sensor_id": "IOT-01",
        "state": "online" if online else "stale",
        "available": online,
        "firmware": row["firmware"],
        "uptime_ms": row["uptime_ms"],
        "last_heartbeat": row["last_heartbeat"],
        "age_seconds": round(age, 1),
    }


@router.get("/observations")
def observations(limit: int = Query(100, ge=1, le=500)):
    db = connect()

    if db is None:
        return {"sensor_id": "IOT-01", "observations": []}

    try:
        rows = db.execute("""
            SELECT *
            FROM observations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return {
            "sensor_id": "IOT-01",
            "observations": [dict(r) for r in rows],
        }
    finally:
        db.close()


@router.get("/devices")
def devices(
    limit: int = Query(100, ge=1, le=500),
    minutes: int = Query(5, ge=1, le=1440),
):
    db = connect()

    if db is None:
        return {"sensor_id": "IOT-01", "devices": []}

    try:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(minutes=minutes)
        ).isoformat()

        rows = db.execute("""
            SELECT
                address,
                address_type,
                COUNT(*) AS sightings,
                MAX(received_at) AS last_seen,
                ROUND(AVG(rssi_dbm), 1) AS avg_rssi,
                COALESCE(
                    (
                        SELECT dn.name
                        FROM device_names AS dn
                        WHERE dn.address = observations.address
                          AND dn.address_type =
                              observations.address_type
                        ORDER BY dn.last_seen DESC
                        LIMIT 1
                    ),
                    MAX(name)
                ) AS advertised_name,
                MIN(received_at) AS first_seen,
                MIN(rssi_dbm) AS min_rssi,
                MAX(rssi_dbm) AS max_rssi,
                (
                    SELECT o2.manufacturer_id
                    FROM observations AS o2
                    WHERE o2.address = observations.address
                      AND o2.address_type = observations.address_type
                      AND o2.manufacturer_id IS NOT NULL
                      AND o2.received_at >= ?
                    ORDER BY o2.id DESC
                    LIMIT 1
                ) AS manufacturer_id
            FROM observations
            WHERE received_at >= ?
            GROUP BY address, address_type
            ORDER BY last_seen DESC
            LIMIT ?
        """, (cutoff, cutoff, limit)).fetchall()

        # JARVIS_IOT_R27A_MANUFACTURER
        companies = {
            0x004C: "Apple",
            0x0075: "Samsung Electronics",
        }

        enriched = []

        for row in rows:
            device = dict(row)
            company_id = device.get("manufacturer_id")

            device["manufacturer"] = (
                companies.get(company_id, "Unknown")
                if company_id is not None
                else "Not advertised"
            )

            device["company_id_hex"] = (
                f"0x{company_id:04X}"
                if company_id is not None
                else None
            )

            enriched.append(device)

        return {
            "sensor_id": "IOT-01",
            "devices": enriched,
        }
    finally:
        db.close()


@router.get("/summary")
def summary():
    db = connect()

    if db is None:
        return {
            "sensor_id": "IOT-01",
            "observations": 0,
            "distinct_addresses": 0,
        }

    try:
        row = db.execute("""
            SELECT
                COUNT(*) AS observations,
                COUNT(DISTINCT address) AS distinct_addresses,
                MIN(rssi_dbm) AS min_rssi,
                MAX(rssi_dbm) AS max_rssi,
                ROUND(AVG(rssi_dbm), 1) AS avg_rssi
            FROM observations
        """).fetchone()

        return {"sensor_id": "IOT-01", **dict(row)}
    finally:
        db.close()


# JARVIS_IOT_R28B_DEVICE_INSPECTOR
# Read-only analysis of retained BLE advertising evidence.

import re as _ble_re
import uuid as _ble_uuid
from fastapi import HTTPException as _BLEHTTPException

_BLE_ADDRESS = _ble_re.compile(
    r"^[0-9a-f]{2}(:[0-9a-f]{2}){5}$"
)

_BLE_SERVICES = {
    "1800": ("Generic Access", None),
    "1801": ("Generic Attribute", None),
    "180a": ("Device Information", None),
    "180d": ("Heart Rate", "Health / fitness sensor"),
    "180f": ("Battery Service", None),
    "1812": ("Human Interface Device", "Input device"),
    "1816": ("Cycling Speed and Cadence", "Cycling sensor"),
    "1818": ("Cycling Power", "Cycling sensor"),
    "181a": ("Environmental Sensing", "Environmental sensor"),
    "181c": ("User Data", None),
    "1826": ("Fitness Machine", "Fitness equipment"),
    "184e": ("Audio Stream Control", "Bluetooth LE Audio"),
    "1850": ("Published Audio Capabilities", "Bluetooth LE Audio"),
    "1853": ("Common Audio", "Bluetooth LE Audio"),
}

def _ble_ad_fields(hex_value):
    try:
        raw = bytes.fromhex(hex_value or "")
    except (ValueError, TypeError):
        return []

    result = []
    i = 0
    while i < len(raw):
        length = raw[i]
        i += 1
        if length == 0:
            break
        if i + length > len(raw):
            break
        kind = raw[i]
        value = raw[i + 1:i + length]
        result.append((kind, value))
        i += length
    return result


def _ble_decode_ad(hex_value):
    services = []
    names = []
    company_ids = []
    fields_present = set()

    for kind, value in _ble_ad_fields(hex_value):
        fields_present.add(f"0x{kind:02X}")

        if kind in (0x08, 0x09) and value:
            names.append({
                "name": value.decode("utf-8", errors="replace")[:64],
                "source": "complete_local_name" if kind == 0x09
                          else "shortened_local_name",
            })

        elif kind in (0x02, 0x03):
            for i in range(0, len(value) - 1, 2):
                services.append(f"{int.from_bytes(value[i:i+2], 'little'):04x}")

        elif kind in (0x04, 0x05):
            for i in range(0, len(value) - 3, 4):
                services.append(f"{int.from_bytes(value[i:i+4], 'little'):08x}")

        elif kind in (0x06, 0x07):
            for i in range(0, len(value) - 15, 16):
                services.append(str(_ble_uuid.UUID(bytes_le=value[i:i+16])))

        elif kind == 0xFF and len(value) >= 2:
            company_ids.append(int.from_bytes(value[:2], "little"))

    return services, names, company_ids, fields_present


@router.get("/device-detail")
def device_detail(
    address: str,
    address_type: int = Query(..., ge=0, le=3),
    limit: int = Query(500, ge=1, le=2000),
):
    address = address.strip().lower()

    if not _BLE_ADDRESS.fullmatch(address):
        raise _BLEHTTPException(400, "Invalid BLE address")

    db = connect()
    if db is None:
        raise _BLEHTTPException(503, "IOT-01 database unavailable")

    try:
        observations = db.execute("""
            SELECT id, received_at, address, address_type,
                   rssi_dbm, name, manufacturer_id,
                   manufacturer_hex, raw_adv_hex,
                   event_type, scan_mode
            FROM observations
            WHERE address = ? AND address_type = ?
            ORDER BY id DESC
            LIMIT ?
        """, (address, address_type, limit)).fetchall()

        if not observations:
            raise _BLEHTTPException(
                404, "No retained observations for this address"
            )

        names = {}
        services = set()
        companies = set()
        fields = set()
        categories = set()
        raw_examples = []
        scan_responses = 0

        for row in observations:
            if row["name"]:
                names.setdefault(
                    row["name"], "collector_observation"
                )

            if row["manufacturer_id"] is not None:
                companies.add(row["manufacturer_id"])

            if row["event_type"] == 4:
                scan_responses += 1

            raw_hex = row["raw_adv_hex"]
            if not raw_hex:
                continue

            srv, discovered_names, ids, kinds = _ble_decode_ad(raw_hex)
            services.update(srv)
            companies.update(ids)
            fields.update(kinds)

            for item in discovered_names:
                names[item["name"]] = item["source"]

            if raw_hex not in raw_examples and len(raw_examples) < 6:
                raw_examples.append(raw_hex)

        # Persistent historical names, if R2.8A is installed.
        table_exists = db.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'device_names'
        """).fetchone()

        if table_exists:
            old_names = db.execute("""
                SELECT name FROM device_names
                WHERE address = ? AND address_type = ?
                ORDER BY last_seen DESC
                LIMIT 20
            """, (address, address_type)).fetchall()
            for row in old_names:
                names.setdefault(row["name"], "historical_observation")

        service_info = []
        for service in sorted(services):
            name, category = _BLE_SERVICES.get(
                service, ("Unclassified service", None)
            )
            service_info.append({
                "uuid": service,
                "description": name,
                "category_hint": category,
            })
            if category:
                categories.add(category)

        company_names = {
            0x004C: "Apple",
            0x0075: "Samsung Electronics",
        }

        signals = [
            {
                "received_at": row["received_at"],
                "rssi_dbm": row["rssi_dbm"],
            }
            for row in reversed(observations)
        ]

        first_seen = observations[-1]["received_at"]
        last_seen = observations[0]["received_at"]

        return {
            "sensor_id": "IOT-01",
            "address": address,
            "address_type": address_type,
            "address_note": (
                "Random address; physical identity may rotate"
                if address_type == 1
                else "Public address type reported by scanner"
                if address_type == 0
                else "See controller address-type documentation"
            ),
            "observations_examined": len(observations),
            "first_seen_retained": first_seen,
            "last_seen": last_seen,
            "rssi": {
                "minimum": min(r["rssi_dbm"] for r in observations),
                "maximum": max(r["rssi_dbm"] for r in observations),
                "average": round(
                    sum(r["rssi_dbm"] for r in observations)
                    / len(observations), 1
                ),
            },
            "names": [
                {"value": name, "source": source}
                for name, source in names.items()
            ],
            "manufacturers": [
                {"id": company, "name": company_names.get(
                    company, "Unclassified company"
                )}
                for company in sorted(companies)
            ],
            "advertised_services": service_info,
            "category_hints": sorted(categories),
            "identification": {
                "status": (
                    "advertised_name_observed" if names
                    else "manufacturer_evidence_only" if companies
                    else "insufficient_evidence"
                ),
                "exact_model_confirmed": False,
            },
            "advertising_data_types": sorted(fields),
            "scan_responses": scan_responses,
            "raw_advertisement_examples": raw_examples,
            "signal_history": signals[-200:],
        }
    finally:
        db.close()
