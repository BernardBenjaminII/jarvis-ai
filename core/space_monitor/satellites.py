from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from threading import RLock
from typing import Any

import requests
from sgp4.api import Satrec, WGS72
from sgp4.conveniences import sat_epoch_datetime


BASE = "https://celestrak.org/NORAD/elements/gp.php"

GROUPS = {
    "stations": "STATIONS",
    "gps": "GPS-OPS",
    "weather": "WEATHER",
}

CACHE_TTL = 900
_TIMEOUT = (5, 20)
_LOCK = RLock()
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc_datetime(value: str) -> datetime:
    """
    Parse ISO timestamps from CelesTrak OMM.

    CelesTrak may supply epochs either with a trailing Z or
    without an explicit timezone. OMM epochs are UTC, so a
    timezone-less value must be treated as UTC rather than as
    local time.
    """

    dt = datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )
    else:
        dt = dt.astimezone(
            timezone.utc
        )

    return dt


def _fetch_group(group: str) -> list[dict[str, Any]]:
    now = time.time()

    with _LOCK:
        cached = _CACHE.get(group)

        if cached and now - cached[0] < CACHE_TTL:
            return cached[1]

    celestrak_group = GROUPS[group]

    response = requests.get(
        BASE,
        params={
            "GROUP": celestrak_group,
            "FORMAT": "JSON",
        },
        headers={
            "User-Agent": "Jarvis-Space-Monitor/8.9A"
        },
        timeout=_TIMEOUT,
    )

    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError(
            f"CelesTrak {group} returned non-list payload"
        )

    with _LOCK:
        _CACHE[group] = (now, payload)

    return payload


def _jday(dt: datetime) -> tuple[float, float]:
    from sgp4.api import jday

    return jday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000,
    )


def _gmst(jd: float) -> float:
    """
    Approximate Greenwich mean sidereal time in radians.
    Good enough for real-time globe positioning.
    """
    t = (jd - 2451545.0) / 36525.0

    deg = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t * t
        - (t * t * t) / 38710000.0
    )

    return math.radians(deg % 360.0)


def _eci_to_geodetic(
    x: float,
    y: float,
    z: float,
    jd: float,
) -> tuple[float, float, float]:
    """
    Convert TEME-ish ECI km coordinates to approximate
    geodetic lon/lat/alt for Cesium display.

    This is suitable for operational visualization, not
    precision orbit determination.
    """

    theta = _gmst(jd)

    x_ecef = (
        math.cos(theta) * x
        + math.sin(theta) * y
    )

    y_ecef = (
        -math.sin(theta) * x
        + math.cos(theta) * y
    )

    z_ecef = z

    a = 6378.137
    e2 = 6.69437999014e-3

    lon = math.atan2(y_ecef, x_ecef)

    r = math.hypot(x_ecef, y_ecef)

    lat = math.atan2(
        z_ecef,
        r * (1.0 - e2),
    )

    for _ in range(6):
        sin_lat = math.sin(lat)

        n = a / math.sqrt(
            1.0 - e2 * sin_lat * sin_lat
        )

        alt = (
            r / max(math.cos(lat), 1e-12)
            - n
        )

        lat = math.atan2(
            z_ecef,
            r * (
                1.0
                - e2 * n / (n + alt)
            ),
        )

    sin_lat = math.sin(lat)

    n = a / math.sqrt(
        1.0 - e2 * sin_lat * sin_lat
    )

    alt = (
        r / max(math.cos(lat), 1e-12)
        - n
    )

    return (
        math.degrees(lon),
        math.degrees(lat),
        alt,
    )


def _satrec_from_omm(row: dict[str, Any]) -> Satrec:
    """
    Construct Satrec directly from CelesTrak JSON/OMM fields.
    """

    sat = Satrec()

    epoch_raw = row["EPOCH"]

    epoch = parse_utc_datetime(
        epoch_raw
    )

    year_start = datetime(
        epoch.year,
        1,
        1,
        tzinfo=timezone.utc,
    )

    epoch_days = (
        epoch - year_start
    ).total_seconds() / 86400.0 + 1.0

    sat.sgp4init(
        WGS72,
        "i",
        int(row["NORAD_CAT_ID"]),
        (epoch - datetime(
            1949, 12, 31,
            tzinfo=timezone.utc
        )).total_seconds() / 86400.0,
        float(row.get("BSTAR", 0.0) or 0.0),
        float(row.get("MEAN_MOTION_DOT", 0.0) or 0.0),
        float(row.get("MEAN_MOTION_DDOT", 0.0) or 0.0),
        float(row["ECCENTRICITY"]),
        math.radians(
            float(row["ARG_OF_PERICENTER"])
        ),
        math.radians(
            float(row["INCLINATION"])
        ),
        math.radians(
            float(row["MEAN_ANOMALY"])
        ),
        float(row["MEAN_MOTION"])
        * 2.0 * math.pi / 1440.0,
        math.radians(
            float(row["RA_OF_ASC_NODE"])
        ),
    )

    return sat


def _position(
    row: dict[str, Any],
    when: datetime,
) -> dict[str, Any] | None:

    try:
        sat = _satrec_from_omm(row)

        jd, fr = _jday(when)

        error, position, velocity = sat.sgp4(
            jd,
            fr,
        )

        if error != 0:
            return None

        lon, lat, alt = _eci_to_geodetic(
            position[0],
            position[1],
            position[2],
            jd + fr,
        )

        speed = math.sqrt(
            velocity[0] ** 2
            + velocity[1] ** 2
            + velocity[2] ** 2
        )

        epoch = row.get("EPOCH")

        age_hours = None

        if epoch:
            epoch_dt = parse_utc_datetime(
                epoch
            )

            age_hours = (
                when - epoch_dt
            ).total_seconds() / 3600.0

        return {
            "norad_id": row.get("NORAD_CAT_ID"),
            "name": row.get("OBJECT_NAME"),
            "object_id": row.get("OBJECT_ID"),

            "longitude": round(lon, 5),
            "latitude": round(lat, 5),
            "altitude_km": round(alt, 2),

            "velocity_km_s": round(speed, 3),

            "inclination_deg": row.get(
                "INCLINATION"
            ),

            "eccentricity": row.get(
                "ECCENTRICITY"
            ),

            "period_minutes": (
                round(
                    1440.0
                    / float(row["MEAN_MOTION"]),
                    2,
                )
                if row.get("MEAN_MOTION")
                else None
            ),

            "element_epoch": epoch,

            "element_age_hours": (
                round(age_hours, 2)
                if age_hours is not None
                else None
            ),

            "position_time":
                when.isoformat(),
        }

    except Exception:
        return None


def satellite_snapshot(
    groups: list[str] | None = None,
) -> dict[str, Any]:

    selected = groups or [
        "stations",
        "gps",
        "weather",
    ]

    invalid = [
        group
        for group in selected
        if group not in GROUPS
    ]

    if invalid:
        raise ValueError(
            f"Unknown satellite group(s): {invalid}"
        )

    when = utc_now()

    output: dict[str, list[dict[str, Any]]] = {}

    sources = []

    for group in selected:
        rows = _fetch_group(group)

        positions = []

        for row in rows:
            pos = _position(
                row,
                when,
            )

            if pos is not None:
                pos["group"] = group
                positions.append(pos)

        output[group] = positions

        sources.append({
            "provider": "CelesTrak",
            "group": GROUPS[group],
            "records": len(rows),
            "positions": len(positions),
            "url":
                f"{BASE}?GROUP={GROUPS[group]}"
                "&FORMAT=JSON",
        })

    return {
        "schema": "jarvis.space.satellites.r8.9a",
        "generated_at": when.isoformat(),
        "groups": output,
        "counts": {
            key: len(value)
            for key, value in output.items()
        },
        "total": sum(
            len(value)
            for value in output.values()
        ),
        "sources": sources,
    }


def satellite_health() -> dict[str, Any]:
    try:
        snapshot = satellite_snapshot()

        return {
            "schema":
                "jarvis.space.satellites.health.r8.9a",

            "status": "healthy",

            "generated_at":
                snapshot["generated_at"],

            "groups":
                snapshot["counts"],

            "total":
                snapshot["total"],
        }

    except Exception as exc:
        return {
            "schema":
                "jarvis.space.satellites.health.r8.9a",

            "status": "unavailable",

            "error":
                f"{type(exc).__name__}: {exc}",
        }



def satellite_orbit_track(
    norad_id: int,
    minutes_back: int = 45,
    minutes_forward: int = 45,
    step_seconds: int = 60,
) -> dict[str, Any]:
    """
    Build a short ground/orbit track for one satellite.

    This is intended for visualization around the currently selected
    object, not for bulk display of every tracked satellite.
    """

    from datetime import timedelta

    target = None
    target_group = None

    for group in GROUPS:
        rows = _fetch_group(group)

        for row in rows:
            if int(row.get("NORAD_CAT_ID", -1)) == int(norad_id):
                target = row
                target_group = group
                break

        if target is not None:
            break

    if target is None:
        raise ValueError(
            f"NORAD object {norad_id} not found in tracked groups"
        )

    sat = _satrec_from_omm(target)
    center = utc_now()

    points = []

    start = center - timedelta(minutes=minutes_back)
    end = center + timedelta(minutes=minutes_forward)

    current = start

    while current <= end:
        jd, fr = _jday(current)

        error, position, velocity = sat.sgp4(
            jd,
            fr,
        )

        if error == 0:
            lon, lat, alt = _eci_to_geodetic(
                position[0],
                position[1],
                position[2],
                jd + fr,
            )

            points.append({
                "time": current.isoformat(),
                "longitude": round(lon, 5),
                "latitude": round(lat, 5),
                "altitude_km": round(alt, 2),
            })

        current += timedelta(seconds=step_seconds)

    return {
        "schema": "jarvis.space.satellite.track.r8.9c",
        "generated_at": center.isoformat(),
        "norad_id": int(norad_id),
        "name": target.get("OBJECT_NAME"),
        "group": target_group,
        "minutes_back": minutes_back,
        "minutes_forward": minutes_forward,
        "step_seconds": step_seconds,
        "points": points,
    }
