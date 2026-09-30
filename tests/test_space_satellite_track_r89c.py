from core.space_monitor.satellites import (
    satellite_orbit_track,
)


def test_satellite_track_live():
    data = satellite_orbit_track(
        25544,
        minutes_back=5,
        minutes_forward=5,
        step_seconds=60,
    )

    assert data["norad_id"] == 25544
    assert len(data["points"]) >= 5

    for point in data["points"]:
        assert -180 <= point["longitude"] <= 180
        assert -90 <= point["latitude"] <= 90
        assert point["altitude_km"] > 100
