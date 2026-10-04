from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.capabilities.adapters.local_sensors import mobile


def iso_age(seconds: float) -> str:
    return (
        datetime.now(timezone.utc)
        - timedelta(seconds=seconds)
    ).isoformat().replace("+00:00", "Z")


def test_event_channels_remain_live_with_fresh_phone_heartbeat():
    packet = {
        "capabilities": ["activity", "pedometer"],
        "activity": {
            "observed_at": iso_age(3600),
            "stationary": True,
        },
        "pedometer": {
            "observed_at": iso_age(3600),
            "steps": 24,
        },
        "device": {
            "observed_at": iso_age(1),
        },
    }

    channels = mobile._sensor_channels(packet)

    assert channels["activity"].state == "live"
    assert channels["pedometer"].state == "live"
    assert channels["activity"].age_seconds > 3500
    assert channels["pedometer"].age_seconds > 3500


def test_event_channels_go_stale_when_phone_heartbeat_stops():
    packet = {
        "capabilities": ["activity", "pedometer"],
        "activity": {
            "observed_at": iso_age(120),
            "stationary": True,
        },
        "pedometer": {
            "observed_at": iso_age(120),
            "steps": 24,
        },
        "device": {
            "observed_at": iso_age(60),
        },
    }

    channels = mobile._sensor_channels(packet)

    assert channels["activity"].state == "stale"
    assert channels["pedometer"].state == "stale"
