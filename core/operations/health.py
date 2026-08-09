"""Health aggregation for the Operations interface."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Any

from core.executive.events import (
    ExecutiveEventBus,
    HealthEventPublisher,
)

from .enums import HealthState
from .models import (
    HealthComponentSnapshot,
    HealthSnapshot,
    Provenance,
    utc_now,
)

HealthProbe = Callable[[], Mapping[str, Any]]


class HealthAggregator:
    """Aggregate probes and publish only aggregate state transitions."""

    def __init__(
        self,
        probes: Mapping[str, HealthProbe] | None = None,
        *,
        event_bus: ExecutiveEventBus | None = None,
    ) -> None:
        self._probes = dict(probes or {})
        self._publisher = (
            HealthEventPublisher(event_bus)
            if event_bus is not None
            else None
        )
        self._last_state: HealthState | None = None

    def collect(
        self,
        *,
        checked_at: datetime | None = None,
    ) -> HealthSnapshot:
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
                state = HealthState(
                    str(result.get("state", "unknown"))
                )
                detail = str(result.get("detail", ""))
            except Exception as exc:
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

        aggregate = self._aggregate_state(
            component.state for component in components
        )
        snapshot = HealthSnapshot(
            state=aggregate,
            components=tuple(components),
            checked_at=now,
        )

        if (
            self._publisher is not None
            and aggregate is not self._last_state
        ):
            self._publisher.publish_transition(
                previous_state=(
                    self._last_state.value
                    if self._last_state is not None
                    else None
                ),
                current_state=aggregate.value,
                checked_at=now,
                components=len(components),
            )

        self._last_state = aggregate
        return snapshot

    @staticmethod
    def _aggregate_state(
        states: Iterable[HealthState],
    ) -> HealthState:
        values = tuple(states)
        if any(
            state is HealthState.UNAVAILABLE
            for state in values
        ):
            return HealthState.UNAVAILABLE
        if any(
            state in (
                HealthState.DEGRADED,
                HealthState.UNKNOWN,
            )
            for state in values
        ):
            return HealthState.DEGRADED
        return HealthState.HEALTHY
