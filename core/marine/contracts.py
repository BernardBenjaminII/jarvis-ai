"""Canonical contracts for JARVIS marine observations."""

from dataclasses import asdict, dataclass
from datetime import datetime


VALID_MODES = {
    "OBSERVED",
    "NOWCAST",
    "FORECAST",
    "PREDICTION",
}

VALID_FRESHNESS = {
    "LIVE",
    "CURRENT",
    "AGED",
    "STALE",
    "UNKNOWN",
}


def iso_utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("marine timestamps must be timezone-aware")

    return (
        value.astimezone()
        .astimezone(__import__("datetime").timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class MarineObservation:
    observation_id: str
    kind: str
    value: float
    unit: str
    latitude: float
    longitude: float
    observed_at: datetime
    received_at: datetime
    provider: str
    station_id: str | None = None
    station_name: str | None = None
    data_mode: str = "OBSERVED"
    freshness: str = "UNKNOWN"
    age_seconds: int | None = None
    direction_degrees: float | None = None
    quality: str | None = None

    def __post_init__(self):
        if not self.observation_id:
            raise ValueError("observation_id is required")

        if not self.kind:
            raise ValueError("kind is required")

        if self.data_mode not in VALID_MODES:
            raise ValueError("invalid marine data_mode")

        if self.freshness not in VALID_FRESHNESS:
            raise ValueError("invalid marine freshness")

        if not -90 <= float(self.latitude) <= 90:
            raise ValueError("invalid latitude")

        if not -180 <= float(self.longitude) <= 180:
            raise ValueError("invalid longitude")

        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")

    def to_dict(self):
        result = asdict(self)
        result["observed_at"] = iso_utc(self.observed_at)
        result["received_at"] = iso_utc(self.received_at)
        return result
