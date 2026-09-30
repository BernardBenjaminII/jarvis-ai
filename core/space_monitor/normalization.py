from __future__ import annotations

from typing import Any


def number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_kp(rows: Any) -> tuple[float | None, str | None]:
    if not isinstance(rows, list) or not rows:
        return None, None

    valid = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("Kp") is not None
    ]

    if not valid:
        return None, None

    row = valid[-1]

    return (
        number(row.get("Kp")),
        row.get("time_tag"),
    )


def normalize_kp_forecast(rows: Any) -> list[dict]:
    if not isinstance(rows, list):
        return []

    out = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        out.append({
            "time": row.get("time_tag"),
            "kp": number(row.get("kp")),
            "observed": row.get("observed"),
            "scale": row.get("noaa_scale"),
        })

    return out


def normalize_alerts(rows: Any, limit: int = 20) -> list[dict]:
    if not isinstance(rows, list):
        return []

    out = []

    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue

        out.append({
            "product_id": row.get("product_id"),
            "issued": row.get("issue_datetime"),
            "message": row.get("message"),
        })

    return out


def normalize_aurora(data: Any) -> dict:
    if not isinstance(data, dict):
        return {}

    coords = data.get("coordinates")

    return {
        "observation_time": data.get("Observation Time"),
        "forecast_time": data.get("Forecast Time"),
        "format": data.get("Data Format"),
        "type": data.get("type"),
        "coordinates": coords if isinstance(coords, list) else [],
    }


def _summary_row(data: Any) -> dict[str, Any]:
    """
    NOAA SWPC summary products currently return:

        [
            {
                "proton_speed": 298,
                "time_tag": "..."
            }
        ]

    rather than a bare dictionary.
    """

    if isinstance(data, list):
        for row in reversed(data):
            if isinstance(row, dict):
                return row

    if isinstance(data, dict):
        return data

    return {}


def _latest_propagated_row(
    data: Any,
) -> dict[str, Any]:
    """
    Convert NOAA's header + row representation into one dictionary.

    Example:

        [
            ["time_tag", "speed", ..., "bt", ...],
            ["...", 296.5, ..., 4.04, ...],
            ...
        ]
    """

    if (
        not isinstance(data, list) or
        len(data) < 2 or
        not isinstance(data[0], list)
    ):
        return {}

    headers = data[0]

    for row in reversed(data[1:]):
        if (
            isinstance(row, list) and
            len(row) == len(headers)
        ):
            return dict(zip(headers, row))

    return {}


def normalize_solar_wind(
    propagated: Any,
    speed_summary: Any,
    mag_summary: Any,
) -> dict:

    speed_row = _summary_row(speed_summary)
    mag_row = _summary_row(mag_summary)
    propagated_row = _latest_propagated_row(
        propagated
    )

    # Prefer NOAA's concise real-time summaries.
    # Fall back to latest propagated values if needed.
    speed = number(
        speed_row.get("proton_speed")
    )

    if speed is None:
        speed = number(
            propagated_row.get("speed")
        )

    bt = number(
        mag_row.get("bt")
    )

    if bt is None:
        bt = number(
            propagated_row.get("bt")
        )

    bz = number(
        mag_row.get("bz_gsm")
    )

    if bz is None:
        bz = number(
            propagated_row.get("bz")
        )

    density = number(
        propagated_row.get("density")
    )

    temperature = number(
        propagated_row.get("temperature")
    )

    return {
        "speed_km_s": speed,
        "magnetic_field_nt": bt,
        "bz_gsm_nt": bz,
        "density_p_cm3": density,
        "temperature_k": temperature,

        "summary_time":
            speed_row.get("time_tag") or
            mag_row.get("time_tag"),

        "propagated_time":
            propagated_row.get(
                "propagated_time_tag"
            ),

        "latest_propagated":
            propagated_row,
    }
