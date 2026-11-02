#!/usr/bin/env python3
"""JARVIS R2.9A — bounded passive Wi-Fi access-point inventory."""

import json
import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scapy.all import (
    PcapReader, Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt
)

# JARVIS_WIFI_R29A_DIRECT_ADAPTER
# Load the existing hardware guard without initializing
# the full JARVIS capability framework.
import importlib.util

_ADAPTER = (
    Path(__file__).resolve().parents[2]
    / "core/capabilities/adapters/local_sensors/wifi.py"
)

_spec = importlib.util.spec_from_file_location(
    "jarvis_wifi_hardware_adapter", _ADAPTER
)

if _spec is None or _spec.loader is None:
    raise RuntimeError("Wi-Fi hardware adapter unavailable")

_wifi_adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wifi_adapter)

_lookup = _wifi_adapter._lookup

DB = Path.home() / ".local/state/jarvis/wifi_ap.sqlite3"
SENSORS = ("WIFI-01", "WIFI-02")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def security_from_rsn(raw):
    """Decode advertised RSN AKM suites, not actual connection security."""
    akms = []
    if len(raw) < 8:
        return akms

    try:
        offset = 2  # RSN version
        offset += 4  # group cipher

        pair_count = int.from_bytes(raw[offset:offset+2], "little")
        offset += 2 + pair_count * 4

        if offset + 2 > len(raw):
            return akms

        akm_count = int.from_bytes(raw[offset:offset+2], "little")
        offset += 2

        if akm_count > 64 or offset + akm_count * 4 > len(raw):
            return akms

        for i in range(akm_count):
            suite = raw[offset + i*4:offset + (i+1)*4]
            akms.append(suite.hex())

    except (ValueError, IndexError):
        pass

    return akms


def classify_security(akms, privacy, rsn_present):
    suites = set(akms)
    psk = "000fac02" in suites
    sae = "000fac08" in suites

    if psk and sae:
        return "WPA2/WPA3-Personal transition advertised"
    if sae:
        return "WPA3-Personal advertised"
    if psk:
        return "WPA2-Personal advertised"
    if rsn_present:
        return "RSN present — other/unknown authentication"
    if privacy:
        return "Privacy advertised — security undetermined"
    return "No privacy capability advertised"


def decode_pcap(filename):
    networks = {}

    with PcapReader(str(filename)) as reader:
        for pkt in reader:
            dot11 = pkt.getlayer(Dot11)
            if dot11 is None:
                continue

            mgmt = pkt.getlayer(Dot11Beacon)
            if mgmt is None:
                mgmt = pkt.getlayer(Dot11ProbeResp)
            if mgmt is None:
                continue

            bssid = (dot11.addr3 or "").lower()
            if not bssid:
                continue

            net = networks.setdefault(bssid, {
                "bssid": bssid,
                "ssid_hex": None,
                "ssid_display": None,
                "channel_ie": None,
                "signal_dbm": None,
                "frames": 0,
                "ssid_observations": {},
                "akms": set(),
                "rsn_present": False,
                "privacy": False,
            })

            net["frames"] += 1
            net["privacy"] |= "privacy" in str(mgmt.cap).lower()

            signal = getattr(pkt, "dBm_AntSignal", None)
            if signal is not None:
                net["signal_dbm"] = int(signal)

            elt = mgmt.payload.getlayer(Dot11Elt)

            while isinstance(elt, Dot11Elt):
                raw = bytes(elt.info)

                if elt.ID == 0:
                    # JARVIS_WIFI_R210A_IDENTITY
                    # Preserve each distinct SSID across captured frames.
                    raw_hex = raw.hex()
                    observations = net["ssid_observations"]
                    observations[raw_hex] = (
                        observations.get(raw_hex, 0) + 1
                    )

                    if raw:
                        try:
                            decoded = raw.decode("utf-8")
                            readable = (
                                decoded
                                if decoded and decoded.isprintable()
                                else None
                            )
                        except UnicodeDecodeError:
                            readable = None

                        net["ssid_hex"] = raw_hex
                        net["ssid_display"] = readable

                elif elt.ID == 3 and raw:
                    net["channel_ie"] = raw[0]

                elif elt.ID == 48:
                    net["rsn_present"] = True
                    net["akms"].update(security_from_rsn(raw))

                elt = elt.payload.getlayer(Dot11Elt)

    for net in networks.values():
        net["security"] = classify_security(
            net["akms"], net["privacy"], net["rsn_present"]
        )
        net["akms"] = sorted(net["akms"])

    return list(networks.values())


def init_db(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS access_points (
            sensor_id TEXT NOT NULL,
            bssid TEXT NOT NULL,
            ssid_hex TEXT,
            ssid_display TEXT,
            channel_ie INTEGER,
            signal_dbm INTEGER,
            security TEXT,
            akms_json TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            frames_seen INTEGER NOT NULL,
            PRIMARY KEY(sensor_id, bssid)
        )
    """)
    db.commit()


def capture(sensor_id):
    spec = _lookup(sensor_id)

    if not spec["available"]:
        raise RuntimeError(f"{sensor_id}: unavailable")

    iface = spec["interface"]

    check = subprocess.run(
        ["iw", "dev", iface, "info"],
        capture_output=True, text=True, timeout=5,
        check=False
    )

    if check.returncode or not any(
        line.strip() == "type monitor"
        for line in check.stdout.splitlines()
    ):
        raise RuntimeError(f"{sensor_id}: not in monitor mode")

    with tempfile.TemporaryDirectory(
        prefix="jarvis-ap-", dir="/tmp"
    ) as tmp:
        pcap = Path(tmp) / "capture.pcap"

        cmd = [
            "/usr/bin/tcpdump",
            "-i", iface,
            "-n", "-s", "1024",
            "-U", "-w", str(pcap),
            "type mgt subtype beacon or "
            "type mgt subtype probe-resp"
        ]

        # JARVIS_WIFI_R29D_GRACEFUL_CAPTURE
        # Stop tcpdump with SIGINT so it closes its PCAP cleanly.
        import signal

        with open(Path(tmp) / "tcpdump.log", "wb") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT
            )

            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)

            if proc.returncode not in (0, -signal.SIGINT):
                print(
                    f"{sensor_id}: tcpdump exited "
                    f"with status {proc.returncode}",
                    flush=True
                )

        if not pcap.exists() or pcap.stat().st_size < 24:
            return []

        return decode_pcap(pcap)



# JARVIS_WIFI_R210A_IDENTITY
def resolve_mac_identity(bssid):
    """Report manufacturer evidence without guessing randomized MACs."""
    import re

    parts = bssid.lower().split(":")
    first_octet = int(parts[0], 16)

    if first_octet & 1:
        return "multicast_or_group", None, None

    if first_octet & 2:
        return "locally_administered", None, None

    prefix = "".join(parts[:3]).upper()
    oui_file = Path("/usr/share/ieee-data/oui.txt")

    if not oui_file.is_file():
        return "globally_administered", prefix, None

    # A simple IEEE MA-L/OUI lookup. Other assignment sizes
    # are not inferred from unmatched prefixes.
    pattern = re.compile(
        r"^([0-9A-F]{6})\\s+\\(base 16\\)\\s+(.+)$"
    )

    with oui_file.open(
        "r", encoding="utf-8", errors="replace"
    ) as handle:
        for line in handle:
            match = pattern.match(line.strip())
            if match and match.group(1) == prefix:
                return (
                    "globally_administered",
                    prefix,
                    match.group(2).strip()
                )

    return "globally_administered", prefix, None


def init_identity_schema(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS wifi_ssid_history (
            sensor_id TEXT NOT NULL,
            bssid TEXT NOT NULL,
            ssid_hex TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            observations INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL,
            PRIMARY KEY(sensor_id, bssid, ssid_hex)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS wifi_ap_identity (
            sensor_id TEXT NOT NULL,
            bssid TEXT NOT NULL,
            mac_class TEXT NOT NULL,
            oui_prefix TEXT,
            manufacturer TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(sensor_id, bssid)
        )
    """)

    # Seed the last SSID retained by older collector versions.
    # Its historic observation count is unknown, so use zero.
    db.execute("""
        INSERT OR IGNORE INTO wifi_ssid_history (
            sensor_id, bssid, ssid_hex,
            first_seen, last_seen,
            observations, source
        )
        SELECT sensor_id, bssid, ssid_hex,
               first_seen, last_seen,
               0, 'legacy_snapshot'
        FROM access_points
        WHERE ssid_hex IS NOT NULL
    """)

    # Include already-known APs, even if not captured today.
    for sensor_id, bssid in db.execute(
        "SELECT sensor_id, bssid FROM access_points"
    ).fetchall():
        record_mac_identity(db, sensor_id, bssid)


def record_mac_identity(db, sensor_id, bssid):
    mac_class, prefix, vendor = resolve_mac_identity(bssid)
    db.execute("""
        INSERT INTO wifi_ap_identity (
            sensor_id, bssid, mac_class,
            oui_prefix, manufacturer, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(sensor_id, bssid) DO UPDATE SET
            mac_class = excluded.mac_class,
            oui_prefix = excluded.oui_prefix,
            manufacturer = excluded.manufacturer,
            updated_at = excluded.updated_at
    """, (
        sensor_id, bssid, mac_class,
        prefix, vendor, utcnow()
    ))


def record_ssid_history(db, sensor_id, net, now):
    for ssid_hex, count in net["ssid_observations"].items():
        db.execute("""
            INSERT INTO wifi_ssid_history (
                sensor_id, bssid, ssid_hex,
                first_seen, last_seen,
                observations, source
            )
            VALUES (?, ?, ?, ?, ?, ?, 'captured')
            ON CONFLICT(sensor_id, bssid, ssid_hex)
            DO UPDATE SET
                last_seen = excluded.last_seen,
                observations = (
                    wifi_ssid_history.observations +
                    excluded.observations
                ),
                source = 'captured'
        """, (
            sensor_id, net["bssid"], ssid_hex,
            now, now, count
        ))



# JARVIS_WIFI_R210B_SIGNAL_HISTORY
WIFI_RSSI_RETENTION_DAYS = 90


def init_signal_history(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS wifi_signal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            bssid TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            channel INTEGER,
            signal_dbm INTEGER NOT NULL,
            frames_observed INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_wifi_signal_lookup
        ON wifi_signal_history (
            sensor_id, bssid, observed_at
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_wifi_signal_retention
        ON wifi_signal_history (observed_at)
    """)


def record_signal_history(db, sensor_id, net, observed_at):
    signal = net.get("signal_dbm")

    # Missing signal data is not a 0 dBm measurement.
    if signal is None:
        return

    db.execute("""
        INSERT INTO wifi_signal_history (
            sensor_id, bssid, observed_at,
            channel, signal_dbm, frames_observed
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        sensor_id,
        net["bssid"],
        observed_at,
        net["channel_ie"],
        int(signal),
        int(net["frames"])
    ))


def prune_signal_history(db):
    from datetime import datetime, timezone, timedelta

    cutoff = (
        datetime.now(timezone.utc) -
        timedelta(days=WIFI_RSSI_RETENTION_DAYS)
    ).isoformat()

    db.execute("""
        DELETE FROM wifi_signal_history
        WHERE observed_at < ?
    """, (cutoff,))

def main():
    DB.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(DB.parent, 0o700)

    with sqlite3.connect(DB) as db:
        init_db(db)
        init_identity_schema(db)
        init_signal_history(db)
        os.chmod(DB, 0o600)

        # JARVIS_WIFI_R29D_FAILURE_REPORTING
        successful_captures = 0
        failed_sensors = []

        for sensor_id in SENSORS:
            print(f"\n=== {sensor_id} ===", flush=True)

            try:
                networks = capture(sensor_id)
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                print("Capture error:", exc, flush=True)
                failed_sensors.append(sensor_id)
                continue

            successful_captures += 1

            now = utcnow()

            for net in networks:
                db.execute("""
                    INSERT INTO access_points (
                        sensor_id, bssid, ssid_hex, ssid_display,
                        channel_ie, signal_dbm, security,
                        akms_json, first_seen, last_seen,
                        frames_seen
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sensor_id, bssid) DO UPDATE SET
                        ssid_hex = COALESCE(
                            excluded.ssid_hex, access_points.ssid_hex
                        ),
                        ssid_display = COALESCE(
                            excluded.ssid_display,
                            access_points.ssid_display
                        ),
                        channel_ie = excluded.channel_ie,
                        signal_dbm = excluded.signal_dbm,
                        security = excluded.security,
                        akms_json = excluded.akms_json,
                        last_seen = excluded.last_seen,
                        frames_seen = (
                            access_points.frames_seen +
                            excluded.frames_seen
                        )
                """, (
                    sensor_id, net["bssid"],
                    net["ssid_hex"], net["ssid_display"],
                    net["channel_ie"], net["signal_dbm"],
                    net["security"], json.dumps(net["akms"]),
                    now, now, net["frames"]
                ))

                record_ssid_history(db, sensor_id, net, now)
                record_mac_identity(db, sensor_id, net["bssid"])
                record_signal_history(db, sensor_id, net, now)

                print(
                    net["ssid_display"] or
                    f"(hidden/undecoded: {net['ssid_hex'] or 'empty'})",
                    "|", net["bssid"],
                    "| CH", net["channel_ie"],
                    "|", net["signal_dbm"], "dBm",
                    "|", net["security"],
                    "|", net["frames"], "frames"
                )

            prune_signal_history(db)
            db.commit()

        total = db.execute(
            "SELECT COUNT(*) FROM access_points"
        ).fetchone()[0]

        print("\nPersistent access-point records:", total)
        print("Database:", DB)

        print("Successful captures:", successful_captures)
        print("Failed sensors:", failed_sensors)

        if successful_captures == 0:
            raise SystemExit(
                "All Wi-Fi sensor captures failed"
            )

        if failed_sensors:
            raise SystemExit(
                "Partial Wi-Fi capture failure: " +
                ", ".join(failed_sensors)
            )


if __name__ == "__main__":
    main()
