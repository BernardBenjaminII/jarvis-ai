"""Authoritative Jarvis observer-location broker."""

from __future__ import annotations

from .models import (
    GPSStatus,
    MobileSensorStatus,
    ObserverStatus,
)


def _valid_coordinates(
    latitude: float | None,
    longitude: float | None,
) -> bool:

    if latitude is None or longitude is None:
        return False

    return (
        -90.0 <= latitude <= 90.0
        and -180.0 <= longitude <= 180.0
    )


def observer_status(
    gps: GPSStatus,
    mobile: MobileSensorStatus,
) -> ObserverStatus:
    """
    Choose the best currently valid observer source.

    R1 priority:
        1. live gpsd GNSS fix
        2. live mobile GNSS fix

    Stale mobile telemetry is deliberately rejected.
    """

    if (
        gps.state == "fix"
        and gps.fix
        and _valid_coordinates(
            gps.latitude,
            gps.longitude,
        )
    ):
        return ObserverStatus(
            state="fix",
            available=True,
            source="gpsd",
            latitude=gps.latitude,
            longitude=gps.longitude,
            altitude_m=gps.altitude_m,
            heading_deg=gps.track_deg,
            speed_mps=gps.speed_mps,
            timestamp=gps.timestamp,
            detail=(
                "Observer position supplied by "
                "live gpsd GNSS fix."
            ),
        )

    if (
        mobile.state == "online"
        and mobile.available
        and not mobile.fix_stale
        and _valid_coordinates(
            mobile.latitude,
            mobile.longitude,
        )
    ):
        return ObserverStatus(
            state="fix",
            available=True,
            source="mobile_gnss",
            node_id=mobile.node_id,
            latitude=mobile.latitude,
            longitude=mobile.longitude,
            altitude_m=mobile.altitude_m,
            heading_deg=mobile.heading_deg,
            speed_mps=mobile.speed_mps,
            horizontal_accuracy_m=(
                mobile.horizontal_accuracy_m
            ),
            timestamp=mobile.observed_at,
            age_seconds=mobile.fix_age_seconds,
            detail=(
                "Observer position supplied by "
                "live mobile GNSS telemetry."
            ),
        )

    reasons: list[str] = []

    if gps.state != "fix":
        reasons.append(
            f"gpsd={gps.state}"
        )

    if mobile.state != "online":
        reasons.append(
            f"mobile={mobile.state}"
        )

    elif mobile.fix_stale:
        reasons.append(
            "mobile_gnss=stale"
        )

    detail = (
        "No live observer position is available."
    )

    if reasons:
        detail += " " + ", ".join(reasons) + "."

    return ObserverStatus(
        state="unavailable",
        available=False,
        detail=detail,
    )
