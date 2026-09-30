from datetime import datetime, timezone

from core.space_monitor.satellites import (
    _position,
)


SAMPLE = {
    "OBJECT_NAME": "GPS TEST",
    "OBJECT_ID": "2000-040A",
    "EPOCH": "2026-09-30T04:17:11.000000",
    "MEAN_MOTION": 2.0056,
    "ECCENTRICITY": 0.0117,
    "INCLINATION": 54.84,
    "RA_OF_ASC_NODE": 10.0,
    "ARG_OF_PERICENTER": 30.0,
    "MEAN_ANOMALY": 45.0,
    "NORAD_CAT_ID": 26407,
    "BSTAR": 0.0,
    "MEAN_MOTION_DOT": 0.0,
    "MEAN_MOTION_DDOT": 0.0,
}


def test_position_is_plausible():
    when = datetime(
        2026,
        9,
        30,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = _position(
        SAMPLE,
        when,
    )

    assert result is not None

    assert -180 <= result["longitude"] <= 180
    assert -90 <= result["latitude"] <= 90

    assert result["altitude_km"] > 100
    assert result["velocity_km_s"] > 0
