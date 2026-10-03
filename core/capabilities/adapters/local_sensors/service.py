"""Combined local-sensor status service."""

from __future__ import annotations

import socket

from .gps import gps_status
from .mobile import mobile_status
from .models import SensorSnapshot
from .observer import observer_status
from .sdr import sdr_status


def sensor_snapshot() -> SensorSnapshot:

    gps = gps_status()
    mobile = mobile_status()

    return SensorSnapshot(
        host=socket.gethostname(),
        sdr=sdr_status(),
        gps=gps,
        mobile=mobile,
        observer=observer_status(
            gps=gps,
            mobile=mobile,
        ),
    )
