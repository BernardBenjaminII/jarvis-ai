from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.capabilities.adapters.local_sensors import mobile


def iso_age(seconds: float) -> str:
    return (
        datetime.now(timezone.utc)
        - timedelta(seconds=seconds)
    ).isoformat().replace("+00:00", "Z")


def test_r3_capabilities_include_advertised_and_legacy_aliases():
    packet = {
        "capabilities": [
            "gnss",
            "compass",
            "accelerometer",
            "gyroscope",
            "magnetometer",
            "device_motion",
            "barometer",
            "relative_altitude",
            "absolute_altitude",
            "activity",
            "pedometer",
            "battery",
            "thermal",
            "proximity",
        ],
        "location": {"latitude": 49.0, "longitude": 8.0},
        "heading": {"true_deg": 90.0},
        "motion": {"observed_at": iso_age(1)},
        "device": {
            "battery_level": 1.0,
            "battery_state": "full",
            "thermal_state": "nominal",
            "proximity_near": False,
        },
    }

    capabilities = mobile._capabilities(packet)

    for name in packet["capabilities"]:
        assert name in capabilities

    assert "heading" in capabilities
    assert "imu" in capabilities


def test_r3_channels_have_independent_freshness():
    packet = {
        "capabilities": [
            "gnss",
            "compass",
            "accelerometer",
            "gyroscope",
            "magnetometer",
            "device_motion",
            "barometer",
            "relative_altitude",
            "absolute_altitude",
            "activity",
            "pedometer",
            "battery",
            "thermal",
            "proximity",
        ],
        "observed_at": iso_age(40),
        "location": {"latitude": 49.0, "longitude": 8.0},
        "heading": {
            "observed_at": iso_age(40),
            "true_deg": 90.0,
        },
        "motion": {"observed_at": iso_age(1)},
        "raw": {
            "accelerometer": {"observed_at": iso_age(1)},
            "gyroscope": {"observed_at": iso_age(1)},
            "magnetometer": {"observed_at": iso_age(1)},
        },
        "environment": {
            "barometer_observed_at": iso_age(1),
            "pressure_kpa": 101.1,
            "relative_altitude_m": 0.3,
            "absolute_altitude_observed_at": iso_age(1),
            "absolute_altitude_m": 98.0,
        },
        "activity": {
            "observed_at": iso_age(90),
            "stationary": True,
        },
        "pedometer": {
            "observed_at": iso_age(90),
            "steps": 24,
        },
        "device": {
            "observed_at": iso_age(1),
            "battery_level": 1.0,
            "thermal_state": "nominal",
            "proximity_near": False,
        },
    }

    channels = mobile._sensor_channels(packet)

    assert channels["gnss"].state == "stale"
    assert channels["accelerometer"].state == "live"
    assert channels["gyroscope"].state == "live"
    assert channels["magnetometer"].state == "live"
    assert channels["device_motion"].state == "live"
    assert channels["barometer"].state == "live"
    assert channels["compass"].state == "live"
    assert channels["activity"].state == "live"
    assert channels["pedometer"].state == "live"
    assert channels["battery"].state == "live"
    assert channels["thermal"].state == "live"
    assert channels["proximity"].state == "live"


def test_missing_advertised_channel_reports_no_data():
    channels = mobile._sensor_channels(
        {"capabilities": ["accelerometer"]}
    )

    assert channels["accelerometer"].available is True
    assert channels["accelerometer"].state == "no_data"


def test_absent_unadvertised_channel_is_unavailable():
    channels = mobile._sensor_channels({})

    assert channels["barometer"].available is False
    assert channels["barometer"].state == "no_data"
