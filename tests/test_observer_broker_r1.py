from core.capabilities.adapters.local_sensors.models import (
    GPSStatus,
    MobileSensorStatus,
)

from core.capabilities.adapters.local_sensors.observer import (
    observer_status,
)


def test_observer_prefers_live_gpsd():

    gps = GPSStatus(
        state="fix",
        available=True,
        fix=True,
        latitude=49.1,
        longitude=8.1,
        altitude_m=110.0,
        speed_mps=1.0,
        track_deg=90.0,
    )

    mobile = MobileSensorStatus(
        state="online",
        available=True,
        node_id="PHONE",
        latitude=49.2,
        longitude=8.2,
    )

    observer = observer_status(
        gps=gps,
        mobile=mobile,
    )

    assert observer.state == "fix"
    assert observer.source == "gpsd"
    assert observer.latitude == 49.1


def test_observer_uses_live_mobile():

    gps = GPSStatus(
        state="no_device",
        available=False,
        fix=False,
    )

    mobile = MobileSensorStatus(
        state="online",
        available=True,
        node_id="XPERION-SENSOR-01",
        latitude=49.99,
        longitude=8.27,
        altitude_m=100.0,
        horizontal_accuracy_m=3.5,
        heading_deg=180.0,
        speed_mps=0.0,
        age_seconds=1.0,
    )

    observer = observer_status(
        gps=gps,
        mobile=mobile,
    )

    assert observer.state == "fix"
    assert observer.available is True
    assert observer.source == "mobile_gnss"

    assert observer.node_id == "XPERION-SENSOR-01"
    assert observer.latitude == 49.99
    assert observer.longitude == 8.27


def test_observer_rejects_stale_mobile():

    gps = GPSStatus(
        state="no_device",
        available=False,
        fix=False,
    )

    mobile = MobileSensorStatus(
        state="stale",
        available=True,
        node_id="XPERION-SENSOR-01",
        latitude=49.99,
        longitude=8.27,
        age_seconds=60.0,
    )

    observer = observer_status(
        gps=gps,
        mobile=mobile,
    )

    assert observer.state == "unavailable"
    assert observer.available is False
    assert observer.source is None


def test_observer_rejects_invalid_coordinates():

    gps = GPSStatus(
        state="no_device",
        available=False,
        fix=False,
    )

    mobile = MobileSensorStatus(
        state="online",
        available=True,
        latitude=999.0,
        longitude=8.27,
    )

    observer = observer_status(
        gps=gps,
        mobile=mobile,
    )

    assert observer.state == "unavailable"
