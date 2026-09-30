from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceStatus:
    name: str
    provider: str
    url: str
    ok: bool
    fetched_at: str
    age_seconds: float | None = None
    error: str | None = None


@dataclass(slots=True)
class SpaceWeatherSnapshot:
    schema: str
    generated_at: str

    kp_current: float | None = None
    kp_time: str | None = None
    kp_forecast: list[dict[str, Any]] = field(default_factory=list)

    scales: dict[str, Any] = field(default_factory=dict)

    solar_wind: dict[str, Any] = field(default_factory=dict)

    alerts: list[dict[str, Any]] = field(default_factory=list)

    aurora: dict[str, Any] = field(default_factory=dict)

    sources: list[SourceStatus] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sources"] = [asdict(x) for x in self.sources]
        return payload
