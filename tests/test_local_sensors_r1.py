"""Tests for JARVIS local sensor normalization."""

from core.capabilities.adapters.local_sensors.gps import (
    _normalize_gps_messages,
)
from core.capabilities.adapters.local_sensors.sdr import (
    _parse_rtl_test_output,
)


def test_sdr_nooelec_smart_v5_ready():
    output = """
Found 1 device(s):
  0:  Nooelec, NESDR SMArt v5, SN: 86182997

Using device 0: Generic RTL2832U OEM
Detached kernel driver
Found Rafael Micro R820T tuner
Sampling at 2048000 S/s.
No E4000 tuner found, aborting.
Reattached kernel driver
"""

    status = _parse_rtl_test_output(output)

    assert status.state == "ready"
    assert status.available is True
    assert status.manufacturer == "Nooelec"
    assert status.product == "NESDR SMArt v5"
    assert status.serial == "86182997"
    assert status.tuner == "Rafael Micro R820T"
    assert status.sample_rate == 2048000


def test_sdr_permission_denied():
    output = """
Found 1 device(s):
  0: Nooelec, NESDR SMArt v5, SN: 86182997
Using device 0: Generic RTL2832U OEM
usb_open error -3
Please fix the device permissions
"""

    status = _parse_rtl_test_output(output)

    assert status.state == "permission_denied"
    assert status.available is True


def test_gps_no_device():
    status = _normalize_gps_messages(
        [
            {"class": "VERSION"},
            {"class": "DEVICES", "devices": []},
        ]
    )

    assert status.state == "no_device"
    assert status.fix is False


def test_gps_connected_without_fix():
    status = _normalize_gps_messages(
        [
            {
                "class": "DEVICES",
                "devices": [{"path": "/dev/ttyUSB0"}],
            },
            {
                "class": "TPV",
                "device": "/dev/ttyUSB0",
                "mode": 1,
            },
        ]
    )

    assert status.state == "no_fix"
    assert status.available is True
    assert status.fix is False


def test_gps_valid_fix():
    status = _normalize_gps_messages(
        [
            {
                "class": "DEVICES",
                "devices": [{"path": "/dev/ttyUSB0"}],
            },
            {
                "class": "TPV",
                "device": "/dev/ttyUSB0",
                "mode": 3,
                "lat": 49.0,
                "lon": 8.0,
                "altMSL": 123.4,
                "speed": 1.5,
                "track": 270.0,
                "time": "2026-10-01T17:00:00.000Z",
            },
        ]
    )

    assert status.state == "fix"
    assert status.fix is True
    assert status.latitude == 49.0
    assert status.longitude == 8.0
    assert status.altitude_m == 123.4
    assert status.speed_mps == 1.5
    assert status.track_deg == 270.0

def test_sensor_route_registered():
    from core.src.main import app

    schema = app.openapi()

    assert "/api/sensors/status" in schema["paths"]
