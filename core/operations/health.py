"""Health aggregation for the Operations interface."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Any

from .enums import HealthState
from .models import HealthComponentSnapshot, HealthSnapshot, Provenance, utc_now

HealthProbe = Callable[[], Mapping[str, Any]]


class HealthAggregator:
    """Aggregates independent component probes into one health snapshot."""

    def __init__(self, probes: Mapping[str, HealthProbe] | None = None) -> None:
        self._probes = dict(probes or {})

    def collect(self, *, checked_at: datetime | None = None) -> HealthSnapshot:
        now = checked_at or utc_now()
        components: list[HealthComponentSnapshot] = []

        if not self._probes:
            components.append(
                HealthComponentSnapshot(
                    component="operations",
                    state=HealthState.HEALTHY,
                    detail="Operations service is available.",
                    checked_at=now,
                    provenance=Provenance(
                        source="operations",
                        source_version="mc1001",
                        captured_at=now,
                    ),
                )
            )

        for component, probe in sorted(self._probes.items()):
            try:
                result = probe()
                state = HealthState(str(result.get("state", "unknown")))
                detail = str(result.get("detail", ""))
            except Exception as exc:  # health boundaries must not crash Operations
                state = HealthState.UNAVAILABLE
                detail = f"{type(exc).__name__}: {exc}"

            components.append(
                HealthComponentSnapshot(
                    component=component,
                    state=state,
                    detail=detail,
                    checked_at=now,
                    provenance=Provenance(
                        source=component,
                        source_version="provider",
                        captured_at=now,
                    ),
                )
            )

        aggregate = self._aggregate_state(component.state for component in components)
        return HealthSnapshot(
            state=aggregate,
            components=tuple(components),
            checked_at=now,
        )

    @staticmethod
    def _aggregate_state(states: Iterable[HealthState]) -> HealthState:
        values = tuple(states)
        if any(state is HealthState.UNAVAILABLE for state in values):
            return HealthState.UNAVAILABLE
        if any(state in (HealthState.DEGRADED, HealthState.UNKNOWN) for state in values):
            return HealthState.DEGRADED
        return HealthState.HEALTHY
