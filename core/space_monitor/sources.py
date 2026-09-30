from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any

import requests


USER_AGENT = "Jarvis-Space-Monitor/8.7"

DEFAULT_TIMEOUT = (5, 15)

URLS = {
    "alerts":
        "https://services.swpc.noaa.gov/products/alerts.json",

    "kp":
        "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",

    "kp_forecast":
        "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json",

    "scales":
        "https://services.swpc.noaa.gov/products/noaa-scales.json",

    "aurora":
        "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json",

    "solar_wind":
        "https://services.swpc.noaa.gov/products/geospace/propagated-solar-wind-1-hour.json",

    "solar_wind_speed_summary":
        "https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json",

    "solar_wind_mag_summary":
        "https://services.swpc.noaa.gov/products/summary/solar-wind-mag-field.json",
}


@dataclass
class CacheEntry:
    stored_at: float
    payload: Any


_CACHE: dict[str, CacheEntry] = {}
_LOCK = RLock()


TTL_SECONDS = {
    "alerts": 120,
    "kp": 120,
    "kp_forecast": 300,
    "scales": 120,
    "aurora": 300,
    "solar_wind": 60,
    "solar_wind_speed_summary": 60,
    "solar_wind_mag_summary": 60,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(
    name: str,
    *,
    force: bool = False,
) -> tuple[Any, dict[str, Any]]:
    if name not in URLS:
        raise KeyError(f"Unknown space source: {name}")

    now = time.time()
    ttl = TTL_SECONDS.get(name, 60)

    with _LOCK:
        cached = _CACHE.get(name)

        if (
            not force
            and cached is not None
            and (now - cached.stored_at) < ttl
        ):
            return cached.payload, {
                "name": name,
                "provider": "NOAA SWPC",
                "url": URLS[name],
                "ok": True,
                "fetched_at": datetime.fromtimestamp(
                    cached.stored_at,
                    tz=timezone.utc,
                ).isoformat(),
                "age_seconds": round(now - cached.stored_at, 2),
                "cached": True,
            }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            URLS[name],
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

        fetched = time.time()

        with _LOCK:
            _CACHE[name] = CacheEntry(
                stored_at=fetched,
                payload=payload,
            )

        return payload, {
            "name": name,
            "provider": "NOAA SWPC",
            "url": URLS[name],
            "ok": True,
            "fetched_at": datetime.fromtimestamp(
                fetched,
                tz=timezone.utc,
            ).isoformat(),
            "age_seconds": 0,
            "cached": False,
        }

    except Exception as exc:
        with _LOCK:
            stale = _CACHE.get(name)

        if stale is not None:
            return stale.payload, {
                "name": name,
                "provider": "NOAA SWPC",
                "url": URLS[name],
                "ok": False,
                "fetched_at": datetime.fromtimestamp(
                    stale.stored_at,
                    tz=timezone.utc,
                ).isoformat(),
                "age_seconds": round(now - stale.stored_at, 2),
                "cached": True,
                "error": f"{type(exc).__name__}: {exc}",
            }

        raise
