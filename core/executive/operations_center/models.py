"""
Canonical contracts for Genesis VII-A0 Pack 1.

These contracts deliberately use the Python standard library only.
They can be serialized directly by the API layer introduced in Pack 2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


def utc_now_iso() -> str:
    """Return an RFC 3339-compatible UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class HealthState(str, Enum):
    """Health state of an observed subsystem."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class MetricState(str, Enum):
    """Availability state of an Executive metric."""

    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"


class StatusState(str, Enum):
    """Aggregated Executive operating status."""

    EXCELLENT = "excellent"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """One independently evaluated health observation."""

    identifier: str
    name: str
    state: HealthState
    observed_value: Any = None
    unit: str | None = None
    message: str = ""
    source: str = ""
    observed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExecutiveHealth:
    """Enterprise health response."""

    overall_state: HealthState
    checks: tuple[HealthCheck, ...]
    generated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_state": self.overall_state.value,
            "checks": [check.to_dict() for check in self.checks],
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class ExecutiveMetric:
    """One measurable Executive value."""

    identifier: str
    name: str
    value: int | float | str | bool | None
    state: MetricState
    source: str
    description: str = ""
    measured_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(frozen=True, slots=True)
class ExecutiveMetrics:
    """Enterprise metrics response."""

    metrics: Mapping[str, ExecutiveMetric]
    generated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": {
                key: metric.to_dict()
                for key, metric in sorted(self.metrics.items())
            },
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class ExecutiveStatus:
    """Derived Executive status summary."""

    overall_state: StatusState
    headline: str
    health_state: HealthState
    available_metrics: int
    unavailable_metrics: int
    configured_metrics: int
    attention_items: tuple[str, ...]
    generated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["overall_state"] = self.overall_state.value
        data["health_state"] = self.health_state.value
        data["attention_items"] = list(self.attention_items)
        return data


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """Unified dashboard payload consumed by the future UI route."""

    health: ExecutiveHealth
    metrics: ExecutiveMetrics
    status: ExecutiveStatus
    generated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "health": self.health.to_dict(),
            "metrics": self.metrics.to_dict(),
            "status": self.status.to_dict(),
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
        }
