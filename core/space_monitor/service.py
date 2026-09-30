from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import SourceStatus, SpaceWeatherSnapshot
from .normalization import (
    latest_kp,
    normalize_alerts,
    normalize_aurora,
    normalize_kp_forecast,
    normalize_solar_wind,
)
from .sources import fetch_json


SOURCE_NAMES = (
    "alerts",
    "kp",
    "kp_forecast",
    "scales",
    "aurora",
    "solar_wind",
    "solar_wind_speed_summary",
    "solar_wind_mag_summary",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_space_weather_snapshot(
    *,
    force: bool = False,
) -> dict[str, Any]:

    raw: dict[str, Any] = {}
    statuses: list[SourceStatus] = []

    for name in SOURCE_NAMES:
        try:
            payload, status = fetch_json(
                name,
                force=force,
            )

            raw[name] = payload

            statuses.append(
                SourceStatus(
                    name=name,
                    provider=status["provider"],
                    url=status["url"],
                    ok=bool(status["ok"]),
                    fetched_at=status["fetched_at"],
                    age_seconds=status.get("age_seconds"),
                    error=status.get("error"),
                )
            )

        except Exception as exc:
            raw[name] = None

            from .sources import URLS

            statuses.append(
                SourceStatus(
                    name=name,
                    provider="NOAA SWPC",
                    url=URLS[name],
                    ok=False,
                    fetched_at=now_utc(),
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    kp_value, kp_time = latest_kp(raw["kp"])

    snapshot = SpaceWeatherSnapshot(
        schema="jarvis.space.weather.r8.7",
        generated_at=now_utc(),

        kp_current=kp_value,
        kp_time=kp_time,

        kp_forecast=normalize_kp_forecast(
            raw["kp_forecast"]
        ),

        scales=(
            raw["scales"]
            if isinstance(raw["scales"], dict)
            else {}
        ),

        solar_wind=normalize_solar_wind(
            raw["solar_wind"],
            raw["solar_wind_speed_summary"],
            raw["solar_wind_mag_summary"],
        ),

        alerts=normalize_alerts(raw["alerts"]),

        aurora=normalize_aurora(raw["aurora"]),

        sources=statuses,
    )

    return snapshot.to_dict()


def space_monitor_health() -> dict[str, Any]:
    snapshot = build_space_weather_snapshot()

    good = sum(
        1
        for src in snapshot["sources"]
        if src["ok"]
    )

    total = len(snapshot["sources"])

    return {
        "schema": "jarvis.space.health.r8.7",
        "generated_at": snapshot["generated_at"],
        "status": (
            "healthy"
            if good == total
            else "degraded"
            if good
            else "unavailable"
        ),
        "sources_ok": good,
        "sources_total": total,
        "sources": snapshot["sources"],
    }
