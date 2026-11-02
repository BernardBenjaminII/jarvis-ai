"""Structured local ADS-B track access for JARVIS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


READSB_DIR = Path("/tmp/jarvis-readsb")
AIRCRAFT_JSON = READSB_DIR / "aircraft.json"
STATS_JSON = READSB_DIR / "stats.json"


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8")
        )
        return value if isinstance(value, dict) else {}
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return value

    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def aircraft_snapshot() -> dict[str, Any]:
    raw = _json(AIRCRAFT_JSON)
    tracks: list[dict[str, Any]] = []

    source_tracks = raw.get("aircraft")

    if not isinstance(source_tracks, list):
        source_tracks = []

    for item in source_tracks:
        if not isinstance(item, dict):
            continue

        seen = _number(item.get("seen"))

        # Ignore stale tracks retained by decoder state.
        if seen is not None and seen > 60:
            continue

        track = {
            "icao": _text(item.get("hex")),
            "callsign": _text(item.get("flight")),
            "registration": _text(item.get("r")),
            "aircraft_type": _text(item.get("t")),
            "description": _text(item.get("desc")),

            "altitude_ft": (
                item.get("alt_baro")
                if item.get("alt_baro") != "ground"
                else 0
            ),
            "on_ground": item.get("alt_baro") == "ground",

            "ground_speed_kt": _number(item.get("gs")),
            "track_deg": _number(item.get("track")),

            "vertical_rate_fpm": (
                _number(item.get("baro_rate"))
                if _number(item.get("baro_rate")) is not None
                else _number(item.get("geom_rate"))
            ),

            "squawk": _text(item.get("squawk")),

            "latitude": _number(item.get("lat")),
            "longitude": _number(item.get("lon")),

            "seen_seconds": seen,
            "messages": _number(item.get("messages")),

            "rssi": _number(item.get("rssi")),
            "category": _text(item.get("category")),
            "emergency": _text(item.get("emergency")),
        }

        tracks.append(track)

    tracks.sort(
        key=lambda x: (
            x.get("seen_seconds")
            if isinstance(
                x.get("seen_seconds"),
                (int, float),
            )
            else 999999
        )
    )

    with_position = sum(
        1
        for track in tracks
        if track.get("latitude") is not None
        and track.get("longitude") is not None
    )

    emergency = sum(
        1
        for track in tracks
        if track.get("squawk")
        in {"7500", "7600", "7700"}
    )

    return {
        "schema_id": "jarvis.rf.adsb.r5",
        "source": "readsb",
        "messages": raw.get("messages", 0),
        "aircraft_count": len(tracks),
        "aircraft_with_position": with_position,
        "emergency_count": emergency,
        "aircraft": tracks,
    }


def adsb_stats() -> dict[str, Any]:
    stats = _json(STATS_JSON)

    latest = (
        stats.get("last1min")
        if isinstance(stats.get("last1min"), dict)
        else {}
    )

    local = (
        latest.get("local")
        if isinstance(latest.get("local"), dict)
        else {}
    )

    return {
        "schema_id": "jarvis.rf.adsb.stats.r5",
        "messages": latest.get("messages", 0),
        "messages_valid": latest.get(
            "messages_valid",
            0,
        ),
        "signal": local.get("signal"),
        "noise": local.get("noise"),
        "peak_signal": local.get("peak_signal"),
        "strong_signals": local.get(
            "strong_signals"
        ),
        "samples_dropped": local.get(
            "samples_dropped"
        ),
        "samples_lost": local.get(
            "samples_lost"
        ),
    }
