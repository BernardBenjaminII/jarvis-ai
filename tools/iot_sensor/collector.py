#!/usr/bin/env python3
"""JARVIS IOT-01 R2.1: passive BLE serial collector."""

import glob
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import serial

SENSOR_ID = "IOT-01"
SERIAL_GLOB = (
    "/dev/serial/by-id/"
    "usb-Espressif_USB_JTAG_serial_debug_unit_"
    "58:E6:C5:C1:48:70-if00"
)

DB_PATH = Path.home() / ".local/state/jarvis/iot01.sqlite3"
MAX_OBSERVATIONS = 10000
ADDRESS_RE = re.compile(r"^[0-9a-f]{2}(:[0-9a-f]{2}){5}$")
HEX_RE = re.compile(r"^[0-9a-fA-F]*$")


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def database():
    DB_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(DB_PATH.parent, 0o700)

    db = sqlite3.connect(DB_PATH, timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY,
            received_at TEXT NOT NULL,
            address TEXT NOT NULL,
            address_type INTEGER NOT NULL,
            rssi_dbm INTEGER NOT NULL,
            name TEXT,
            manufacturer_id INTEGER,
            manufacturer_hex TEXT,
            uptime_ms INTEGER NOT NULL
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS iot01_address_idx
        ON observations(address, received_at)
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS health (
            sensor_id TEXT PRIMARY KEY,
            last_heartbeat TEXT,
            firmware TEXT,
            uptime_ms INTEGER
        )
    """)
    # JARVIS_IOT_R28A_NAMES
    db.execute("""
        CREATE TABLE IF NOT EXISTS device_names (
            address TEXT NOT NULL,
            address_type INTEGER NOT NULL,
            name TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            sightings INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (address, address_type, name)
        )
    """)

    # Recover names still present in the observation window.
    db.execute("""
        INSERT OR IGNORE INTO device_names
            (address, address_type, name,
             first_seen, last_seen, sightings)
        SELECT address, address_type, name,
               MIN(received_at), MAX(received_at), COUNT(*)
        FROM observations
        WHERE name IS NOT NULL AND TRIM(name) != ''
        GROUP BY address, address_type, name
    """)

    db.commit()
    os.chmod(DB_PATH, 0o600)
    return db


def decode_hex(value, limit=512):
    if not isinstance(value, str):
        raise ValueError("invalid hexadecimal field")
    if len(value) > limit or len(value) % 2 or not HEX_RE.fullmatch(value):
        raise ValueError("invalid hexadecimal field")
    return bytes.fromhex(value)


def process(db, message):
    if not isinstance(message, dict):
        return None

    if message.get("sensor_id") != SENSOR_ID:
        return None

    kind = message.get("type")
    schema = message.get("schema")

    if kind == "heartbeat" and schema == "jarvis.iot.health.r1":
        uptime = int(message["uptime_ms"])
        firmware = str(message.get("firmware", ""))[:64]

        if uptime < 0:
            raise ValueError("negative uptime")

        db.execute("""
            INSERT INTO health
                (sensor_id, last_heartbeat, firmware, uptime_ms)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(sensor_id) DO UPDATE SET
                last_heartbeat=excluded.last_heartbeat,
                firmware=excluded.firmware,
                uptime_ms=excluded.uptime_ms
        """, (SENSOR_ID, timestamp(), firmware, uptime))
        db.commit()
        return "heartbeat"

    if kind != "ble_observation" or schema != "jarvis.iot.ble.r1":
        return None

    address = str(message["address"]).lower()
    address_type = int(message["address_type"])
    rssi = int(message["rssi_dbm"])
    uptime = int(message["uptime_ms"])

    if not ADDRESS_RE.fullmatch(address):
        raise ValueError("invalid BLE address")

    if address_type not in (0, 1, 2, 3):
        raise ValueError("invalid BLE address type")

    if not -127 <= rssi <= 20 or uptime < 0:
        raise ValueError("invalid BLE observation values")

    name_bytes = decode_hex(message.get("name_hex", ""))
    manufacturer = decode_hex(message.get("manufacturer_hex", ""))

    name = name_bytes.decode("utf-8", errors="replace")[:64]
    manufacturer_id = (
        int.from_bytes(manufacturer[:2], "little")
        if len(manufacturer) >= 2 else None
    )

    # JARVIS_IOT_R11_STORAGE
    raw_adv = decode_hex(
        message.get("raw_adv_hex", ""), limit=512
    )

    event_type = message.get("event_type")
    if event_type is not None:
        event_type = int(event_type)
        if not 0 <= event_type <= 255:
            raise ValueError("Invalid BLE event type")

    scan_mode = message.get("scan_mode")
    if scan_mode not in (None, "passive", "active"):
        raise ValueError("Invalid BLE scan mode")

    # Preserve observed names independently of the rolling
    # advertisement history.
    if name.strip():
        seen_at = timestamp()

        db.execute("""
            INSERT INTO device_names (
                address, address_type, name,
                first_seen, last_seen, sightings
            )
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(address, address_type, name)
            DO UPDATE SET
                last_seen = excluded.last_seen,
                sightings = device_names.sightings + 1
        """, (
            address, address_type, name,
            seen_at, seen_at
        ))

    db.execute("""
        INSERT INTO observations (
            received_at, address, address_type, rssi_dbm,
            name, manufacturer_id, manufacturer_hex, uptime_ms,
            raw_adv_hex, event_type, scan_mode
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp(), address, address_type, rssi,
        name or None, manufacturer_id,
        manufacturer.hex(), uptime,
        raw_adv.hex() if raw_adv else None,
        event_type, scan_mode
    ))

    return "observation"


def main():
    db = database()
    total = 0
    pending = 0
    last_commit = time.monotonic()
    last_prune = time.monotonic()

    print(f"[IOT-01] Database: {DB_PATH}", flush=True)

    try:
        while True:
            matches = glob.glob(SERIAL_GLOB)

            if not matches:
                print("[IOT-01] Waiting for ESP32-C6", flush=True)
                time.sleep(3)
                continue

            try:
                with serial.Serial(
                    matches[0],
                    baudrate=115200,
                    timeout=1,
                    exclusive=True
                ) as port:
                    print("[IOT-01] Serial connected", flush=True)

                    while True:
                        raw = port.readline()

                        if raw and len(raw) <= 4096:
                            try:
                                msg = json.loads(raw.decode("utf-8"))
                                result = process(db, msg)

                                if result == "observation":
                                    total += 1
                                    pending += 1
                                    if total % 100 == 0:
                                        print(
                                            f"[IOT-01] {total} observations",
                                            flush=True
                                        )
                            except (ValueError, TypeError, KeyError,
                                    UnicodeError, json.JSONDecodeError):
                                pass

                        now = time.monotonic()

                        if pending >= 100 or now - last_commit >= 2:
                            db.commit()
                            pending = 0
                            last_commit = now

                        if now - last_prune >= 30:
                            db.commit()
                            pending = 0

                            db.execute(
                                "DELETE FROM observations "
                                "WHERE id <= COALESCE("
                                "(SELECT MAX(id) - ? "
                                "FROM observations), 0)",
                                (MAX_OBSERVATIONS,),
                            )
                            db.commit()
                            last_prune = now

            except (serial.SerialException, OSError) as exc:
                print(f"[IOT-01] Serial unavailable: {exc}", flush=True)
                db.commit()
                time.sleep(3)

    except KeyboardInterrupt:
        print("\n[IOT-01] Collector stopped", flush=True)
    finally:
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
