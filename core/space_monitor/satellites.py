from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from threading import RLock
from pathlib import Path
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


MIRROR_BASE = (
    "https://raw.githubusercontent.com/"
    "satvisorcom/satvisor-data/master/"
    "celestrak/json"
)

MIRROR_GROUPS = {
    "stations": "stations.json",
    "gps": "gps-ops.json",
    "weather": "weather.json",
}

CACHE_TTL = 7200
STALE_CACHE_TTL = 7 * 24 * 60 * 60

CACHE_DIR = Path(
    os.environ.get(
        "JARVIS_SATELLITE_CACHE_DIR",
        "/mnt/jarvis_runtime/cache/satellites",
    )
)
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


def _cache_file(group: str) -> Path:
    return CACHE_DIR / f"{group}.json"


def _load_disk_cache(
    group: str,
) -> tuple[float, list[dict[str, Any]]] | None:
    path = _cache_file(group)

    try:
        raw = json.loads(path.read_text())

        fetched_at = float(raw["fetched_at"])
        payload = raw["payload"]

        if not isinstance(payload, list):
            return None

        return fetched_at, payload

    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None


def _save_disk_cache(
    group: str,
    fetched_at: float,
    payload: list[dict[str, Any]],
) -> None:
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = _cache_file(group)
    temporary = destination.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            {
                "fetched_at": fetched_at,
                "payload": payload,
            },
            separators=(",", ":"),
        )
    )

    temporary.replace(destination)


def _fetch_mirror_group(
    group: str,
) -> list[dict[str, Any]]:
    """
    Fetch CelesTrak-compatible OMM JSON from the
    GitHub mirror when direct CelesTrak access fails.
    """

    filename = MIRROR_GROUPS[group]

    url = (
        f"{MIRROR_BASE}/{filename}"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent":
                "Jarvis-Space-Monitor/8.9A"
        },
        timeout=_TIMEOUT,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError(
            f"Satellite mirror {group} returned "
            "non-list payload"
        )

    rows = [
        row
        for row in payload
        if isinstance(row, dict)
    ]

    if not rows:
        raise ValueError(
            f"Satellite mirror {group} "
            "returned no records"
        )

    fetched_at = time.time()

    with _LOCK:
        _CACHE[group] = (
            fetched_at,
            rows,
        )

    try:
        _save_disk_cache(
            group,
            fetched_at,
            rows,
        )
    except OSError:
        pass

    return rows


def _fetch_group(group: str) -> list[dict[str, Any]]:
    now = time.time()

    # -----------------------------------------------------
    # Level 1 — RAM cache
    # -----------------------------------------------------

    with _LOCK:
        cached = _CACHE.get(group)

        if cached and now - cached[0] < CACHE_TTL:
            return cached[1]

    # -----------------------------------------------------
    # Level 2 — persistent disk cache
    # -----------------------------------------------------

    disk_cached = _load_disk_cache(group)

    if disk_cached:
        fetched_at, payload = disk_cached

        if now - fetched_at < CACHE_TTL:
            with _LOCK:
                _CACHE[group] = (
                    fetched_at,
                    payload,
                )

            return payload

    # -----------------------------------------------------
    # Level 3 — live CelesTrak
    # -----------------------------------------------------

    celestrak_group = GROUPS[group]

    try:
        response = requests.get(
            BASE,
            params={
                "GROUP": celestrak_group,
                "FORMAT": "JSON",
            },
            headers={
                "User-Agent":
                    "Jarvis-Space-Monitor/8.9A"
            },
            timeout=_TIMEOUT,
        )

        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list):
            raise ValueError(
                f"CelesTrak {group} returned "
                "non-list payload"
            )

        fetched_at = time.time()

        with _LOCK:
            _CACHE[group] = (
                fetched_at,
                payload,
            )

        try:
            _save_disk_cache(
                group,
                fetched_at,
                payload,
            )
        except OSError:
            # Satellite service must remain operational
            # even if persistent-cache storage fails.
            pass

        return payload

    except (
        requests.RequestException,
        ValueError,
    ) as direct_error:

        # -------------------------------------------------
        # Level 4 — GitHub CelesTrak-compatible mirror
        # -------------------------------------------------

        try:
            return _fetch_mirror_group(
                group
            )

        except (
            requests.RequestException,
            ValueError,
        ) as mirror_error:

            # ---------------------------------------------
            # Level 5 — stale last-known-good disk cache
            # ---------------------------------------------

            if disk_cached:
                fetched_at, payload = (
                    disk_cached
                )

                if (
                    now - fetched_at
                    <= STALE_CACHE_TTL
                ):

                    # Prevent every browser refresh from
                    # retrying both upstream sources.
                    with _LOCK:
                        _CACHE[group] = (
                            now,
                            payload,
                        )

                    return payload

            raise RuntimeError(
                "Satellite acquisition failed "
                f"for {group}: "
                f"CelesTrak={type(direct_error).__name__}: "
                f"{direct_error}; "
                f"mirror={type(mirror_error).__name__}: "
                f"{mirror_error}"
            ) from mirror_error

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



# ============================================================================
# JARVIS SPACE R8.9D — OBSERVER GEOMETRY / PASS PREDICTION
# ============================================================================

def _geodetic_to_ecef(
    latitude_deg: float,
    longitude_deg: float,
    altitude_km: float = 0.0,
) -> tuple[float, float, float]:
    """
    WGS-84 geodetic coordinates -> ECEF kilometers.
    """

    lat = math.radians(latitude_deg)
    lon = math.radians(longitude_deg)

    a = 6378.137
    e2 = 6.69437999014e-3

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)

    n = a / math.sqrt(
        1.0 - e2 * sin_lat * sin_lat
    )

    x = (
        n + altitude_km
    ) * cos_lat * math.cos(lon)

    y = (
        n + altitude_km
    ) * cos_lat * math.sin(lon)

    z = (
        n * (1.0 - e2)
        + altitude_km
    ) * sin_lat

    return x, y, z


def _eci_to_ecef_xyz(
    x: float,
    y: float,
    z: float,
    jd: float,
) -> tuple[float, float, float]:
    theta = _gmst(jd)

    return (
        math.cos(theta) * x
        + math.sin(theta) * y,

        -math.sin(theta) * x
        + math.cos(theta) * y,

        z,
    )


def _topocentric(
    satellite_ecef: tuple[float, float, float],
    observer_latitude: float,
    observer_longitude: float,
    observer_altitude_km: float,
) -> dict[str, float]:
    """
    ECEF satellite position -> observer azimuth/elevation/range.
    """

    sx, sy, sz = satellite_ecef

    ox, oy, oz = _geodetic_to_ecef(
        observer_latitude,
        observer_longitude,
        observer_altitude_km,
    )

    dx = sx - ox
    dy = sy - oy
    dz = sz - oz

    lat = math.radians(
        observer_latitude
    )

    lon = math.radians(
        observer_longitude
    )

    east = (
        -math.sin(lon) * dx
        + math.cos(lon) * dy
    )

    north = (
        -math.sin(lat)
        * math.cos(lon)
        * dx
        - math.sin(lat)
        * math.sin(lon)
        * dy
        + math.cos(lat)
        * dz
    )

    up = (
        math.cos(lat)
        * math.cos(lon)
        * dx
        + math.cos(lat)
        * math.sin(lon)
        * dy
        + math.sin(lat)
        * dz
    )

    range_km = math.sqrt(
        east * east
        + north * north
        + up * up
    )

    if range_km <= 0:
        raise ValueError(
            "Invalid observer/satellite range"
        )

    elevation = math.degrees(
        math.asin(
            max(
                -1.0,
                min(
                    1.0,
                    up / range_km,
                ),
            )
        )
    )

    azimuth = (
        math.degrees(
            math.atan2(
                east,
                north,
            )
        )
        + 360.0
    ) % 360.0

    return {
        "azimuth_deg":
            round(azimuth, 2),

        "elevation_deg":
            round(elevation, 2),

        "range_km":
            round(range_km, 2),
    }


def _find_satellite_row(
    norad_id: int,
) -> tuple[str, dict[str, Any]]:
    for group in GROUPS:
        for row in _fetch_group(group):
            if int(
                row.get(
                    "NORAD_CAT_ID",
                    -1,
                )
            ) == int(norad_id):
                return group, row

    raise ValueError(
        f"NORAD object {norad_id} "
        "not found in tracked groups"
    )


def _look_angle(
    sat: Satrec,
    when: datetime,
    observer_latitude: float,
    observer_longitude: float,
    observer_altitude_km: float,
) -> dict[str, Any] | None:

    jd, fr = _jday(when)

    error, position, velocity = sat.sgp4(
        jd,
        fr,
    )

    if error != 0:
        return None

    ecef = _eci_to_ecef_xyz(
        position[0],
        position[1],
        position[2],
        jd + fr,
    )

    look = _topocentric(
        ecef,
        observer_latitude,
        observer_longitude,
        observer_altitude_km,
    )

    look["time"] = when.isoformat()

    return look


def satellite_pass_prediction(
    norad_id: int,
    observer_latitude: float,
    observer_longitude: float,
    observer_altitude_m: float = 0.0,
    hours: float = 24.0,
    min_elevation_deg: float = 0.0,
    step_seconds: int = 30,
) -> dict[str, Any]:
    """
    Predict the next horizon pass for one tracked satellite.

    This is operational visualization / planning output based on
    current CelesTrak orbital elements and SGP4 propagation.
    """

    from datetime import timedelta

    group, row = _find_satellite_row(
        norad_id
    )

    sat = _satrec_from_omm(row)

    observer_altitude_km = (
        observer_altitude_m
        / 1000.0
    )

    start = utc_now()

    current = _look_angle(
        sat,
        start,
        observer_latitude,
        observer_longitude,
        observer_altitude_km,
    )

    if current is None:
        raise ValueError(
            "Unable to propagate current satellite position"
        )

    threshold = float(
        min_elevation_deg
    )

    currently_visible = (
        current["elevation_deg"]
        >= threshold
    )

    active = currently_visible

    rise_time = (
        start.isoformat()
        if currently_visible
        else None
    )

    rise_azimuth = (
        current["azimuth_deg"]
        if currently_visible
        else None
    )

    peak_time = (
        start.isoformat()
        if currently_visible
        else None
    )

    peak_elevation = (
        current["elevation_deg"]
        if currently_visible
        else -90.0
    )

    peak_azimuth = (
        current["azimuth_deg"]
        if currently_visible
        else None
    )

    set_time = None
    set_azimuth = None

    previous = current

    end = (
        start
        + timedelta(
            hours=max(
                0.25,
                min(
                    float(hours),
                    72.0,
                ),
            )
        )
    )

    when = (
        start
        + timedelta(
            seconds=step_seconds
        )
    )

    while when <= end:
        look = _look_angle(
            sat,
            when,
            observer_latitude,
            observer_longitude,
            observer_altitude_km,
        )

        if look is None:
            when += timedelta(
                seconds=step_seconds
            )
            continue

        elevation = look[
            "elevation_deg"
        ]

        prev_elevation = previous[
            "elevation_deg"
        ]

        if (
            not active
            and prev_elevation < threshold
            and elevation >= threshold
        ):
            active = True

            rise_time = look["time"]
            rise_azimuth = look[
                "azimuth_deg"
            ]

            peak_time = look["time"]
            peak_elevation = elevation
            peak_azimuth = look[
                "azimuth_deg"
            ]

        if active:
            if elevation > peak_elevation:
                peak_elevation = elevation
                peak_time = look["time"]
                peak_azimuth = look[
                    "azimuth_deg"
                ]

            if (
                prev_elevation >= threshold
                and elevation < threshold
            ):
                set_time = look["time"]
                set_azimuth = look[
                    "azimuth_deg"
                ]
                break

        previous = look

        when += timedelta(
            seconds=step_seconds
        )

    next_pass = None

    if rise_time is not None:
        next_pass = {
            "rise_time": rise_time,
            "rise_azimuth_deg":
                round(
                    rise_azimuth,
                    2,
                )
                if rise_azimuth is not None
                else None,

            "peak_time": peak_time,
            "max_elevation_deg":
                round(
                    peak_elevation,
                    2,
                ),

            "peak_azimuth_deg":
                round(
                    peak_azimuth,
                    2,
                )
                if peak_azimuth is not None
                else None,

            "set_time": set_time,

            "set_azimuth_deg":
                round(
                    set_azimuth,
                    2,
                )
                if set_azimuth is not None
                else None,
        }

    return {
        "schema":
            "jarvis.space.satellite.pass.r8.9d",

        "generated_at":
            start.isoformat(),

        "norad_id":
            int(norad_id),

        "name":
            row.get("OBJECT_NAME"),

        "group":
            group,

        "observer": {
            "latitude":
                observer_latitude,

            "longitude":
                observer_longitude,

            "altitude_m":
                observer_altitude_m,

            "min_elevation_deg":
                threshold,
        },

        "current": current,

        "currently_above_threshold":
            currently_visible,

        "next_pass":
            next_pass,

        "prediction_hours":
            hours,

        "element_epoch":
            row.get("EPOCH"),
    }


def satellites_above_observer(
    observer_latitude: float,
    observer_longitude: float,
    observer_altitude_m: float = 0.0,
    min_elevation_deg: float = 0.0,
) -> dict[str, Any]:
    """
    Current tracked satellites above observer threshold.
    """

    when = utc_now()

    observer_altitude_km = (
        observer_altitude_m
        / 1000.0
    )

    visible: list[
        dict[str, Any]
    ] = []

    counts = {
        "stations": 0,
        "gps": 0,
        "weather": 0,
    }

    total_catalog = 0

    for group in GROUPS:
        rows = _fetch_group(group)

        total_catalog += len(rows)

        for row in rows:
            try:
                sat = _satrec_from_omm(
                    row
                )

                look = _look_angle(
                    sat,
                    when,
                    observer_latitude,
                    observer_longitude,
                    observer_altitude_km,
                )

                if look is None:
                    continue

                if (
                    look["elevation_deg"]
                    < min_elevation_deg
                ):
                    continue

                counts[group] += 1

                visible.append({
                    "norad_id":
                        row.get(
                            "NORAD_CAT_ID"
                        ),

                    "name":
                        row.get(
                            "OBJECT_NAME"
                        ),

                    "group":
                        group,

                    "azimuth_deg":
                        look[
                            "azimuth_deg"
                        ],

                    "elevation_deg":
                        look[
                            "elevation_deg"
                        ],

                    "range_km":
                        look[
                            "range_km"
                        ],

                    "element_epoch":
                        row.get("EPOCH"),
                })

            except Exception:
                continue

    visible.sort(
        key=lambda item:
            item["elevation_deg"],
        reverse=True,
    )

    return {
        "schema":
            "jarvis.space.observer.r8.9d",

        "generated_at":
            when.isoformat(),

        "observer": {
            "latitude":
                observer_latitude,

            "longitude":
                observer_longitude,

            "altitude_m":
                observer_altitude_m,

            "min_elevation_deg":
                min_elevation_deg,
        },

        "catalog_total":
            total_catalog,

        "visible_total":
            len(visible),

        "counts":
            counts,

        "visible":
            visible,
    }
