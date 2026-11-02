"""JARVIS Wi-Fi sensors R1A: guarded inventory and bounded passive AP observation."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Hardware MAC address is checked in addition to an interface lookup.
SENSORS = {
    'WIFI-01': {'mac': '24:ec:99:9b:27:c7', 'chipset': 'AR9271', 'driver': 'ath9k_htc'},
    'WIFI-02': {'mac': '00:c0:ca:b8:4a:4a', 'chipset': 'RTL8814AU', 'driver': 'rtl8814au'},
}
PROTECTED_INTERFACE = 'wlp5s0'
INTERFACE_ROOT = Path('/sys/class/net')


def _driver_name(iface: str) -> str | None:
    try:
        return (INTERFACE_ROOT / iface / 'device' / 'driver').resolve(strict=True).name
    except (OSError, RuntimeError):
        return None


def _lookup(sensor_id: str) -> dict:
    if sensor_id not in SENSORS:
        raise ValueError('Unknown sensor ID')
    spec = SENSORS[sensor_id]
    for address_file in INTERFACE_ROOT.glob('*/address'):
        try:
            iface = address_file.parent.name
            if iface == PROTECTED_INTERFACE:
                continue
            if address_file.read_text().strip().lower() == spec['mac']:
                driver = _driver_name(iface)
                # Driver checks avoid accidentally operating on similarly named interfaces.
                if driver != spec['driver']:
                    return {'id': sensor_id, 'chipset': spec['chipset'], 'state': 'driver_mismatch',
                            'interface': iface, 'driver': driver, 'available': False}
                return {'id': sensor_id, 'chipset': spec['chipset'], 'state': 'ready',
                        'interface': iface, 'driver': driver, 'available': True}
        except OSError:
            continue
    return {'id': sensor_id, 'chipset': spec['chipset'], 'state': 'unavailable',
            'interface': None, 'driver': None, 'available': False}


def inventory() -> dict:
    return {'schema': 'jarvis.wifi.r1a', 'host': os.uname().nodename,
            'sensors': [_lookup(sensor_id) for sensor_id in SENSORS]}


def capture(sensor_id: str, seconds: int = 10) -> dict:
    """Capture only beacon/probe-response management frames; no raw payload persistence."""
    if not 1 <= seconds <= 15:
        raise ValueError('Capture seconds must be between 1 and 15')
    sensor = _lookup(sensor_id)
    if not sensor['available']:
        raise ValueError(f"Sensor unavailable: {sensor['state']}")
    iface = sensor['interface']
    if not shutil.which('iw') or not shutil.which('tcpdump'):
        raise RuntimeError('Requires iw and tcpdump')
    mode = subprocess.run(['iw', 'dev', iface, 'info'], capture_output=True, text=True,
                          timeout=5, check=False)
    if mode.returncode != 0 or not re.search(r'^\s*type monitor\s*$', mode.stdout, re.M):
        raise ValueError('Sensor must already be in monitor mode')
    # Timeout bounds the capture even when nothing is received. No shell or packet injection.
    cmd = ['tcpdump', '-i', iface, '-l', '-e', '-n', '-s', '512',
           'type mgt subtype beacon or type mgt subtype probe-resp']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=seconds,
                                check=False, errors='replace')
        output = result.stdout
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b''
        if isinstance(output, bytes):
            output = output.decode('utf-8', 'replace')
    observed = {}
    for line in output.splitlines():
        bssid = re.search(r'BSSID:([0-9a-f:]{17})', line, re.I)
        frame = re.search(r'\b(Beacon|Probe Response)\s*\(([^)]*)\)', line)
        if not bssid or not frame:
            continue
        dbm = re.search(r'(-?\d+)dBm signal', line)
        mhz = re.search(r'(\d{4}) MHz', line)
        key = bssid.group(1).lower()
        prior = observed.get(key)
        if prior is None:
            observed[key] = {'bssid': key, 'ssid': frame.group(2) or None,
                             'signal_dbm': int(dbm.group(1)) if dbm else None,
                             'frequency_mhz': int(mhz.group(1)) if mhz else None,
                             'frames_seen': 1}
        else:
            prior['frames_seen'] += 1
    return {'schema': 'jarvis.wifi.observations.r1a', 'id': sensor_id,
            'observed_at': datetime.now(timezone.utc).isoformat(),
            'duration_seconds': seconds, 'observations': list(observed.values())}
