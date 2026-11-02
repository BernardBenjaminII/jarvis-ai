#!/usr/bin/env python3
"""JARVIS R2.12A — read-only local device identity discovery."""

import json
import re
import sqlite3
import subprocess
import socket
from datetime import datetime, timezone
from pathlib import Path

DB = Path.home() / ".local/state/jarvis/lan_identity.sqlite3"
INTERFACE = "wlp5s0"


def now():
    return datetime.now(timezone.utc).isoformat()


def command(args, timeout=8):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def get_neighbors():
    raw = command(
        ["ip", "-j", "-4", "neigh", "show", "dev", INTERFACE],
        timeout=3,
    )
    try:
        rows = json.loads(raw)
    except ValueError:
        return []

    return [
        {
            "ip": row["dst"],
            "mac": row["lladdr"].lower(),
            "state": row.get("state", []),
        }
        for row in rows
        if row.get("dst") and row.get("lladdr")
    ]


def get_mdns():
    """Parse Avahi resolved services without probing IP ranges."""
    raw = command(
        ["avahi-browse", "-art"],
        timeout=12,
    )

    devices = {}
    current = None

    def finish():
        if not current:
            return
        ip = current.get("ip")
        # JARVIS_R212C_LOOPBACK_FILTER
        if not ip or ":" in ip or ip.startswith("127."):
            return

        entry = devices.setdefault(
            ip, {"ip": ip, "hostname": None, "services": set()}
        )
        if current.get("hostname"):
            entry["hostname"] = current["hostname"]

        if current.get("service"):
            entry["services"].add(current["service"])

    for line in raw.splitlines():
        if line.startswith("= "):
            finish()
            current = {
                "service": line.split("  ", 1)[-1].strip(),
            }
        elif current is not None:
            match = re.search(r"hostname = \[(.+?)\]", line)
            if match:
                current["hostname"] = match.group(1)

            match = re.search(r"address = \[(.+?)\]", line)
            if match:
                current["ip"] = match.group(1)

    finish()

    return {
        ip: {
            **record,
            "services": sorted(record["services"]),
        }
        for ip, record in devices.items()
    }


def classify(hostname, services):
    name = (hostname or "").lower()
    combined = " ".join(services).lower()

    if "macbook" in name or "macbook" in combined:
        return "computer", "mDNS hostname"

    if "android" in name:
        return "mobile_device", "mDNS hostname"

    if "printer" in name or "ipp" in combined:
        return "printer_candidate", "Service evidence"

    if "apple-tv" in name or "appletv" in name:
        return "media_device", "mDNS hostname"

    return "unknown", "Unclassified"


def init_database(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS lan_devices (
            device_key TEXT PRIMARY KEY,
            ip TEXT,
            mac TEXT,
            hostname TEXT,
            display_name TEXT,
            device_type TEXT,
            identity_source TEXT,
            services_json TEXT NOT NULL DEFAULT '[]',
            neighbor_state_json TEXT NOT NULL DEFAULT '[]',
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_lan_devices_ip
        ON lan_devices(ip)
    """)


def main():
    neighbors = get_neighbors()
    mdns = get_mdns()

    gateway_raw = command(
        ["ip", "-4", "route", "show", "default"],
        timeout=3,
    )
    gateway_match = re.search(
        r"\bvia\s+(\d+\.\d+\.\d+\.\d+)", gateway_raw
    )
    gateway = gateway_match.group(1) if gateway_match else None

    by_ip = {}

    for neighbor in neighbors:
        by_ip[neighbor["ip"]] = {
            **neighbor,
            "hostname": None,
            "services": [],
        }

    for ip, record in mdns.items():
        entry = by_ip.setdefault(
            ip,
            {
                "ip": ip,
                "mac": None,
                "state": [],
                "hostname": None,
                "services": [],
            },
        )
        entry["hostname"] = record["hostname"]
        entry["services"] = record["services"]

    timestamp = now()
    DB.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    with sqlite3.connect(DB) as db:
        init_database(db)

        for ip, entry in sorted(by_ip.items()):
            hostname = entry["hostname"]
            mac = entry["mac"]
            services = entry["services"]

            device_type, source = classify(hostname, services)

            if ip == gateway:
                name = "DeepWater gateway"
                device_type = "gateway"
                source = "Default route"
            elif hostname:
                name = hostname.removesuffix(".local")
            else:
                name = "Unidentified LAN device"

            # MAC-based records survive DHCP address changes.
            # IP-only records remain provisional.
            key = "mac:" + mac if mac else "ip:" + ip

            db.execute("""
                INSERT INTO lan_devices (
                    device_key, ip, mac, hostname,
                    display_name, device_type, identity_source,
                    services_json, neighbor_state_json,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_key) DO UPDATE SET
                    ip = excluded.ip,
                    hostname = COALESCE(
                        excluded.hostname, lan_devices.hostname
                    ),
                    display_name = CASE
                        WHEN excluded.hostname IS NOT NULL
                          OR excluded.device_type = 'gateway'
                        THEN excluded.display_name
                        ELSE lan_devices.display_name
                    END,
                    device_type = CASE
                        WHEN excluded.device_type != 'unknown'
                        THEN excluded.device_type
                        ELSE lan_devices.device_type
                    END,
                    identity_source = CASE
                        WHEN excluded.device_type != 'unknown'
                        THEN excluded.identity_source
                        ELSE lan_devices.identity_source
                    END,
                    services_json = excluded.services_json,
                    neighbor_state_json = excluded.neighbor_state_json,
                    last_seen = excluded.last_seen
            """, (
                key, ip, mac, hostname, name,
                device_type, source,
                json.dumps(services),
                json.dumps(entry["state"]),
                timestamp, timestamp,
            ))

            print(
                f"{ip:16} "
                f"{(mac or 'MAC unknown'):20} "
                f"{name:32} "
                f"[{device_type}]"
            )

        db.commit()

        print("\nDatabase:", DB)
        print("Discovered this run:", len(by_ip))
        print(
            "Persistent records:",
            db.execute(
                "SELECT COUNT(*) FROM lan_devices"
            ).fetchone()[0],
        )


if __name__ == "__main__":
    main()
