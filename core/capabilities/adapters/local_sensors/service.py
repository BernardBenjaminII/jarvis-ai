"""Combined local-sensor status service."""

from __future__ import annotations

import socket

from .gps import gps_status
from .models import SensorSnapshot
from .sdr import sdr_status


def sensor_snapshot() -> SensorSnapshot:
    return SensorSnapshot(
        host=socket.gethostname(),
        sdr=sdr_status(),
        gps=gps_status(),
    )
