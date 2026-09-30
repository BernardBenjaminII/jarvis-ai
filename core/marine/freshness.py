"""Freshness classification for marine observations."""

THRESHOLDS = {
    "water_level": (900, 3600, 21600),
    "water_temperature": (1800, 7200, 43200),
    "wind": (900, 3600, 21600),
    "air_pressure": (1800, 7200, 43200),
    "visibility": (1800, 7200, 21600),
    "current": (900, 3600, 21600),
    "wave_height": (1800, 7200, 21600),
}


def age_seconds(observed_at, received_at):
    return max(0, int((received_at - observed_at).total_seconds()))


def classify(kind, age):
    live, current, aged = THRESHOLDS.get(
        kind,
        (1800, 7200, 43200),
    )

    if age <= live:
        return "LIVE"
    if age <= current:
        return "CURRENT"
    if age <= aged:
        return "AGED"
    return "STALE"
