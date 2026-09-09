"""
Executive Operations Center services for Genesis VII-A0 Pack 1.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .collectors import (
    HostHealthCollector,
    MetricsCollector,
    RuntimePaths,
    worst_health_state,
)
from .models import (
    DashboardSnapshot,
    ExecutiveHealth,
    ExecutiveMetrics,
    ExecutiveStatus,
    HealthState,
    MetricState,
    StatusState,
)


T = TypeVar("T")


@dataclass(slots=True)
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class TimedCache(Generic[T]):
    """Small thread-safe monotonic cache for expensive live collectors."""

    def __init__(self, ttl_seconds: float) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must not be negative.")

        self._ttl_seconds = ttl_seconds
        self._entry: _CacheEntry[T] | None = None
        self._lock = threading.RLock()

    def get_or_create(self, factory: Callable[[], T]) -> T:
        with self._lock:
            now = time.monotonic()

            if self._entry and now < self._entry.expires_at:
                return self._entry.value

            value = factory()

            # TTL begins when collection completes, not when it starts.
            # Expensive collectors must not produce entries that are already
            # expired by the time their result becomes available.
            expires_at = time.monotonic() + self._ttl_seconds

            self._entry = _CacheEntry(
                value=value,
                expires_at=expires_at,
            )
            return value

    def invalidate(self) -> None:
        with self._lock:
            self._entry = None


class ExecutiveHealthService:
    """Produce current Executive host and runtime health."""

    def __init__(
        self,
        *,
        paths: RuntimePaths | None = None,
        collector: HostHealthCollector | None = None,
        cache_ttl_seconds: float = 3.0,
    ) -> None:
        resolved_paths = paths or RuntimePaths.from_environment()
        self._collector = collector or HostHealthCollector(resolved_paths)
        self._cache: TimedCache[ExecutiveHealth] = TimedCache(
            cache_ttl_seconds
        )

    def snapshot(self, *, force_refresh: bool = False) -> ExecutiveHealth:
        if force_refresh:
            self._cache.invalidate()

        return self._cache.get_or_create(self._collect)

    def _collect(self) -> ExecutiveHealth:
        checks = self._collector.collect()
        return ExecutiveHealth(
            overall_state=worst_health_state(
                check.state for check in checks
            ),
            checks=checks,
        )


class ExecutiveMetricsService:
    """Produce live Executive metrics without fabricated fallback values."""

    def __init__(
        self,
        *,
        paths: RuntimePaths | None = None,
        collector: MetricsCollector | None = None,
        cache_ttl_seconds: float = 60.0,
    ) -> None:
        resolved_paths = paths or RuntimePaths.from_environment()
        self._collector = collector or MetricsCollector(resolved_paths)
        self._cache: TimedCache[ExecutiveMetrics] = TimedCache(
            cache_ttl_seconds
        )

    def snapshot(self, *, force_refresh: bool = False) -> ExecutiveMetrics:
        if force_refresh:
            self._cache.invalidate()

        return self._cache.get_or_create(self._collect)

    def _collect(self) -> ExecutiveMetrics:
        return ExecutiveMetrics(metrics=self._collector.collect())


class ExecutiveStatusService:
    """Derive an Executive operating judgment from health and metrics."""

    def derive(
        self,
        *,
        health: ExecutiveHealth,
        metrics: ExecutiveMetrics,
    ) -> ExecutiveStatus:
        values = tuple(metrics.metrics.values())

        available = sum(
            1 for metric in values
            if metric.state is MetricState.AVAILABLE
        )
        not_configured = sum(
            1 for metric in values
            if metric.state is MetricState.NOT_CONFIGURED
        )
        unavailable = sum(
            1 for metric in values
            if metric.state is MetricState.UNAVAILABLE
        )

        attention: list[str] = []

        for check in health.checks:
            if check.state in {
                HealthState.DEGRADED,
                HealthState.CRITICAL,
                HealthState.UNAVAILABLE,
            }:
                attention.append(
                    f"{check.name}: {check.message or check.state.value}"
                )

        for metric in values:
            if metric.state is MetricState.UNAVAILABLE:
                attention.append(
                    f"{metric.name}: authoritative source unavailable"
                )

        if health.overall_state is HealthState.CRITICAL:
            overall = StatusState.CRITICAL
            headline = "Executive operations require immediate attention."
        elif health.overall_state in {
            HealthState.DEGRADED,
            HealthState.UNAVAILABLE,
        } or unavailable:
            overall = StatusState.DEGRADED
            headline = "Executive operations are active with deficiencies."
        elif health.overall_state is HealthState.HEALTHY:
            if not_configured:
                overall = StatusState.OPERATIONAL
                headline = (
                    "Executive operations are healthy; additional registries "
                    "remain to be connected."
                )
            else:
                overall = StatusState.EXCELLENT
                headline = "Executive operations are healthy and observable."
        else:
            overall = StatusState.UNKNOWN
            headline = "Executive operating status cannot be fully determined."

        return ExecutiveStatus(
            overall_state=overall,
            headline=headline,
            health_state=health.overall_state,
            available_metrics=available,
            unavailable_metrics=unavailable,
            configured_metrics=len(values) - not_configured,
            attention_items=tuple(attention),
        )


class ExecutiveDashboardService:
    """Aggregate Pack 1 services into one canonical dashboard snapshot."""

    def __init__(
        self,
        *,
        health_service: ExecutiveHealthService | None = None,
        metrics_service: ExecutiveMetricsService | None = None,
        status_service: ExecutiveStatusService | None = None,
    ) -> None:
        self._health_service = (
            health_service or ExecutiveHealthService()
        )
        self._metrics_service = (
            metrics_service or ExecutiveMetricsService()
        )
        self._status_service = status_service or ExecutiveStatusService()

    def snapshot(
        self,
        *,
        force_refresh: bool = False,
    ) -> DashboardSnapshot:
        health = self._health_service.snapshot(
            force_refresh=force_refresh
        )
        metrics = self._metrics_service.snapshot(
            force_refresh=force_refresh
        )
        status = self._status_service.derive(
            health=health,
            metrics=metrics,
        )

        return DashboardSnapshot(
            health=health,
            metrics=metrics,
            status=status,
        )
