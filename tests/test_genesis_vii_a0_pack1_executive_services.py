from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.executive.operations_center.collectors import (
    MetricsCollector,
    RegistryCounter,
    RuntimePaths,
    worst_health_state,
)
from core.executive.operations_center.models import (
    ExecutiveHealth,
    ExecutiveMetric,
    ExecutiveMetrics,
    HealthCheck,
    HealthState,
    MetricState,
    StatusState,
)
from core.executive.operations_center.services import (
    ExecutiveDashboardService,
    ExecutiveHealthService,
    ExecutiveMetricsService,
    ExecutiveStatusService,
    TimedCache,
)


class StubHealthCollector:
    def __init__(self) -> None:
        self.calls = 0

    def collect(self) -> tuple[HealthCheck, ...]:
        self.calls += 1
        return (
            HealthCheck(
                identifier="runtime",
                name="Runtime",
                state=HealthState.HEALTHY,
                observed_value=True,
                source="test",
            ),
        )


class StubMetricsCollector:
    def __init__(self) -> None:
        self.calls = 0

    def collect(self) -> dict[str, ExecutiveMetric]:
        self.calls += 1
        return {
            "assets": ExecutiveMetric(
                identifier="assets",
                name="Assets",
                value=7,
                state=MetricState.AVAILABLE,
                source="test",
            )
        }


class GenesisVIIA0Pack1Tests(unittest.TestCase):
    def test_worst_health_state(self) -> None:
        self.assertEqual(
            worst_health_state(
                (
                    HealthState.HEALTHY,
                    HealthState.DEGRADED,
                    HealthState.CRITICAL,
                )
            ),
            HealthState.CRITICAL,
        )

    def test_timed_cache_reuses_value(self) -> None:
        cache: TimedCache[object] = TimedCache(60)
        calls = 0

        def factory() -> object:
            nonlocal calls
            calls += 1
            return object()

        first = cache.get_or_create(factory)
        second = cache.get_or_create(factory)

        self.assertIs(first, second)
        self.assertEqual(calls, 1)

    def test_health_service_uses_cache(self) -> None:
        collector = StubHealthCollector()
        service = ExecutiveHealthService(
            collector=collector,  # type: ignore[arg-type]
            cache_ttl_seconds=60,
        )

        first = service.snapshot()
        second = service.snapshot()

        self.assertIs(first, second)
        self.assertEqual(collector.calls, 1)
        self.assertEqual(first.overall_state, HealthState.HEALTHY)

    def test_metrics_service_uses_cache(self) -> None:
        collector = StubMetricsCollector()
        service = ExecutiveMetricsService(
            collector=collector,  # type: ignore[arg-type]
            cache_ttl_seconds=60,
        )

        first = service.snapshot()
        second = service.snapshot()

        self.assertIs(first, second)
        self.assertEqual(collector.calls, 1)
        self.assertEqual(first.metrics["assets"].value, 7)

    def test_status_service_reports_operational_when_unconfigured(self) -> None:
        health = ExecutiveHealth(
            overall_state=HealthState.HEALTHY,
            checks=(),
        )
        metrics = ExecutiveMetrics(
            metrics={
                "assets": ExecutiveMetric(
                    identifier="assets",
                    name="Assets",
                    value=None,
                    state=MetricState.NOT_CONFIGURED,
                    source="JARVIS_ASSET_REGISTRY",
                )
            }
        )

        status = ExecutiveStatusService().derive(
            health=health,
            metrics=metrics,
        )

        self.assertEqual(status.overall_state, StatusState.OPERATIONAL)
        self.assertEqual(status.configured_metrics, 0)
        self.assertEqual(status.unavailable_metrics, 0)

    def test_status_service_reports_critical_health(self) -> None:
        health = ExecutiveHealth(
            overall_state=HealthState.CRITICAL,
            checks=(
                HealthCheck(
                    identifier="disk",
                    name="Disk",
                    state=HealthState.CRITICAL,
                    message="Disk full.",
                ),
            ),
        )
        metrics = ExecutiveMetrics(metrics={})

        status = ExecutiveStatusService().derive(
            health=health,
            metrics=metrics,
        )

        self.assertEqual(status.overall_state, StatusState.CRITICAL)
        self.assertTrue(status.attention_items)

    def test_registry_counter_json_array(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets.json"
            path.write_text(
                json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]),
                encoding="utf-8",
            )

            self.assertEqual(
                RegistryCounter().count(path=path),
                3,
            )

    def test_registry_counter_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(
                '{"id": 1}\n\n{"id": 2}\n',
                encoding="utf-8",
            )

            self.assertEqual(
                RegistryCounter().count(path=path),
                2,
            )

    def test_metrics_collector_reads_configured_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            runtime = root / "runtime"
            knowledge = root / "knowledge"
            project.mkdir()
            runtime.mkdir()
            knowledge.mkdir()

            registry = root / "assets.json"
            registry.write_text(
                json.dumps({"assets": [{"id": 1}, {"id": 2}]}),
                encoding="utf-8",
            )

            paths = RuntimePaths(
                project_root=project,
                runtime_root=runtime,
                knowledge_root=knowledge,
            )

            with patch.dict(
                os.environ,
                {"JARVIS_ASSET_REGISTRY": str(registry)},
                clear=False,
            ):
                metrics = MetricsCollector(paths).collect()

            self.assertEqual(
                metrics["assets"].state,
                MetricState.AVAILABLE,
            )
            self.assertEqual(metrics["assets"].value, 2)

    def test_dashboard_snapshot_serializes(self) -> None:
        health_collector = StubHealthCollector()
        metrics_collector = StubMetricsCollector()

        dashboard = ExecutiveDashboardService(
            health_service=ExecutiveHealthService(
                collector=health_collector,  # type: ignore[arg-type]
                cache_ttl_seconds=0,
            ),
            metrics_service=ExecutiveMetricsService(
                collector=metrics_collector,  # type: ignore[arg-type]
                cache_ttl_seconds=0,
            ),
        )

        payload = dashboard.snapshot().to_dict()

        self.assertIn("health", payload)
        self.assertIn("metrics", payload)
        self.assertIn("status", payload)
        self.assertEqual(
            payload["metrics"]["metrics"]["assets"]["value"],
            7,
        )


if __name__ == "__main__":
    unittest.main()
