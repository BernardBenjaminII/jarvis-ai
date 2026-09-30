from core.space_monitor.satellites import (
    _geodetic_to_ecef,
    _topocentric,
)


def test_overhead_geometry():
    observer_lat = 0.0
    observer_lon = 0.0

    sat_ecef = _geodetic_to_ecef(
        0.0,
        0.0,
        500.0,
    )

    look = _topocentric(
        sat_ecef,
        observer_lat,
        observer_lon,
        0.0,
    )

    assert look["elevation_deg"] > 89.0
    assert 499.0 < look["range_km"] < 501.0
