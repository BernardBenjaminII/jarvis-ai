"""
Live collectors for Genesis VII-A0 Pack 1.

No placeholder values are generated. A metric is reported as not_configured
or unavailable when no authoritative source has been configured.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import ExecutiveMetric, HealthCheck, HealthState, MetricState


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Resolved JARVIS runtime and storage locations."""

    project_root: Path
    runtime_root: Path
    knowledge_root: Path

    @classmethod
    def from_environment(cls) -> "RuntimePaths":
        return cls(
            project_root=Path(
                os.environ.get("JARVIS_PROJECT_ROOT", os.getcwd())
            ).resolve(),
            runtime_root=Path(
                os.environ.get(
                    "JARVIS_RUNTIME_ROOT",
                    "/media/abdullah/JARVIS_RUNTIME_L",
                )
            ),
            knowledge_root=Path(
                os.environ.get(
                    "JARVIS_KNOWLEDGE_ROOT",
                    "/media/abdullah/JARVISDATA/Knowledge",
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class RegistrySpecification:
    """A configurable authoritative metric source."""

    metric_id: str
    name: str
    env_path: str
    env_table: str | None
    description: str


REGISTRY_SPECIFICATIONS: tuple[RegistrySpecification, ...] = (
    RegistrySpecification(
        "missions",
        "Missions",
        "JARVIS_MISSION_REGISTRY",
        "JARVIS_MISSION_TABLE",
        "Registered Executive missions.",
    ),
    RegistrySpecification(
        "assets",
        "Assets",
        "JARVIS_ASSET_REGISTRY",
        "JARVIS_ASSET_TABLE",
        "Registered Executive assets.",
    ),
    RegistrySpecification(
        "executive_events",
        "Executive Events",
        "JARVIS_EVENT_REGISTRY",
        "JARVIS_EVENT_TABLE",
        "Published Executive events.",
    ),
    RegistrySpecification(
        "ai_models",
        "AI Models",
        "JARVIS_AI_REGISTRY",
        "JARVIS_AI_TABLE",
        "Registered artificial-intelligence models.",
    ),
    RegistrySpecification(
        "robots",
        "Robots",
        "JARVIS_ROBOT_REGISTRY",
        "JARVIS_ROBOT_TABLE",
        "Registered robotic assets.",
    ),
    RegistrySpecification(
        "digital_twins",
        "Digital Twins",
        "JARVIS_DIGITAL_TWIN_REGISTRY",
        "JARVIS_DIGITAL_TWIN_TABLE",
        "Registered Executive Digital Twins.",
    ),
    RegistrySpecification(
        "organizations",
        "Organizations",
        "JARVIS_ORGANIZATION_REGISTRY",
        "JARVIS_ORGANIZATION_TABLE",
        "Registered constitutional organizations.",
    ),
    RegistrySpecification(
        "background_jobs",
        "Background Jobs",
        "JARVIS_JOB_REGISTRY",
        "JARVIS_JOB_TABLE",
        "Registered or active background jobs.",
    ),
)


class HostHealthCollector:
    """Collect live host, filesystem, and runtime observations."""

    def __init__(self, paths: RuntimePaths) -> None:
        self._paths = paths

    def collect(self) -> tuple[HealthCheck, ...]:
        checks = [
            self._project_root_check(),
            self._runtime_root_check(),
            self._knowledge_root_check(),
            self._root_disk_check(),
            self._project_disk_check(),
            self._memory_check(),
            self._load_check(),
            self._python_check(),
        ]
        return tuple(checks)

    def _path_check(
        self,
        identifier: str,
        name: str,
        path: Path,
    ) -> HealthCheck:
        if not path.exists():
            return HealthCheck(
                identifier=identifier,
                name=name,
                state=HealthState.UNAVAILABLE,
                observed_value=str(path),
                message="Configured path does not exist.",
                source="filesystem",
            )

        if not path.is_dir():
            return HealthCheck(
                identifier=identifier,
                name=name,
                state=HealthState.CRITICAL,
                observed_value=str(path),
                message="Configured path exists but is not a directory.",
                source="filesystem",
            )

        readable = os.access(path, os.R_OK)
        writable = os.access(path, os.W_OK)

        if readable and writable:
            state = HealthState.HEALTHY
            message = "Directory is available, readable, and writable."
        elif readable:
            state = HealthState.DEGRADED
            message = "Directory is readable but not writable."
        else:
            state = HealthState.CRITICAL
            message = "Directory is not readable."

        return HealthCheck(
            identifier=identifier,
            name=name,
            state=state,
            observed_value=str(path),
            message=message,
            source="filesystem",
        )

    def _project_root_check(self) -> HealthCheck:
        return self._path_check(
            "project_root",
            "Project Root",
            self._paths.project_root,
        )

    def _runtime_root_check(self) -> HealthCheck:
        return self._path_check(
            "runtime_root",
            "Runtime Root",
            self._paths.runtime_root,
        )

    def _knowledge_root_check(self) -> HealthCheck:
        return self._path_check(
            "knowledge_root",
            "Knowledge Root",
            self._paths.knowledge_root,
        )

    @staticmethod
    def _disk_check(
        identifier: str,
        name: str,
        path: Path,
    ) -> HealthCheck:
        probe = path
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent

        try:
            usage = shutil.disk_usage(probe)
        except OSError as exc:
            return HealthCheck(
                identifier=identifier,
                name=name,
                state=HealthState.UNAVAILABLE,
                observed_value=str(probe),
                message=f"Unable to read disk usage: {exc}",
                source="shutil.disk_usage",
            )

        used_percent = (
            ((usage.total - usage.free) / usage.total) * 100
            if usage.total
            else 0.0
        )

        if used_percent >= 95:
            state = HealthState.CRITICAL
        elif used_percent >= 85:
            state = HealthState.DEGRADED
        else:
            state = HealthState.HEALTHY

        return HealthCheck(
            identifier=identifier,
            name=name,
            state=state,
            observed_value=round(used_percent, 2),
            unit="percent",
            message=f"{usage.free} bytes free on {probe}.",
            source="shutil.disk_usage",
        )

    def _root_disk_check(self) -> HealthCheck:
        return self._disk_check(
            "root_disk",
            "Root Filesystem",
            Path("/"),
        )

    def _project_disk_check(self) -> HealthCheck:
        return self._disk_check(
            "project_disk",
            "Project Filesystem",
            self._paths.project_root,
        )

    @staticmethod
    def _memory_check() -> HealthCheck:
        meminfo = Path("/proc/meminfo")
        if not meminfo.exists():
            return HealthCheck(
                identifier="memory",
                name="System Memory",
                state=HealthState.UNKNOWN,
                message="/proc/meminfo is unavailable.",
                source="/proc/meminfo",
            )

        values: dict[str, int] = {}
        try:
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                key, raw_value = line.split(":", 1)
                value = int(raw_value.strip().split()[0])
                values[key] = value
        except (OSError, ValueError, IndexError) as exc:
            return HealthCheck(
                identifier="memory",
                name="System Memory",
                state=HealthState.UNAVAILABLE,
                message=f"Unable to parse memory information: {exc}",
                source="/proc/meminfo",
            )

        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", 0)
        if total <= 0:
            state = HealthState.UNKNOWN
            used_percent = None
        else:
            used_percent = ((total - available) / total) * 100
            if used_percent >= 95:
                state = HealthState.CRITICAL
            elif used_percent >= 85:
                state = HealthState.DEGRADED
            else:
                state = HealthState.HEALTHY

        return HealthCheck(
            identifier="memory",
            name="System Memory",
            state=state,
            observed_value=(
                round(used_percent, 2)
                if used_percent is not None
                else None
            ),
            unit="percent",
            message=f"{available} KiB available of {total} KiB.",
            source="/proc/meminfo",
        )

    @staticmethod
    def _load_check() -> HealthCheck:
        try:
            one, five, fifteen = os.getloadavg()
        except (AttributeError, OSError) as exc:
            return HealthCheck(
                identifier="system_load",
                name="System Load",
                state=HealthState.UNKNOWN,
                message=f"Load average unavailable: {exc}",
                source="os.getloadavg",
            )

        cpu_count = os.cpu_count() or 1
        normalized = one / cpu_count

        if normalized >= 2.0:
            state = HealthState.CRITICAL
        elif normalized >= 1.0:
            state = HealthState.DEGRADED
        else:
            state = HealthState.HEALTHY

        return HealthCheck(
            identifier="system_load",
            name="System Load",
            state=state,
            observed_value={
                "one_minute": round(one, 2),
                "five_minutes": round(five, 2),
                "fifteen_minutes": round(fifteen, 2),
                "logical_cpus": cpu_count,
            },
            message="Load averages normalized against logical CPU count.",
            source="os.getloadavg",
        )

    @staticmethod
    def _python_check() -> HealthCheck:
        return HealthCheck(
            identifier="python_runtime",
            name="Python Runtime",
            state=HealthState.HEALTHY,
            observed_value=sys.version.split()[0],
            message=sys.executable,
            source="sys",
        )


class RegistryCounter:
    """Count records in configured JSON, JSONL, text, directory, or SQLite sources."""

    def count(
        self,
        *,
        path: Path,
        table: str | None = None,
    ) -> int:
        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_dir():
            return sum(1 for item in path.rglob("*") if item.is_file())

        suffix = path.suffix.lower()

        if suffix in {".sqlite", ".sqlite3", ".db"}:
            if not table:
                raise ValueError(
                    f"SQLite source {path} requires a configured table name."
                )
            return self._count_sqlite(path, table)

        if suffix == ".json":
            return self._count_json(path)

        if suffix in {".jsonl", ".ndjson"}:
            return self._count_nonempty_lines(path)

        if suffix in {".txt", ".csv", ".tsv"}:
            return self._count_nonempty_lines(path)

        raise ValueError(f"Unsupported registry source: {path}")

    @staticmethod
    def _count_sqlite(path: Path, table: str) -> int:
        if not table.replace("_", "").isalnum():
            raise ValueError("Unsafe SQLite table name.")

        uri = f"file:{path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            row = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()

        return int(row[0]) if row else 0

    @staticmethod
    def _count_json(path: Path) -> int:
        payload = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(payload, list):
            return len(payload)

        if isinstance(payload, dict):
            for key in (
                "items",
                "records",
                "results",
                "assets",
                "missions",
                "events",
                "models",
                "objects",
            ):
                value = payload.get(key)
                if isinstance(value, list):
                    return len(value)
            return len(payload)

        raise ValueError("JSON registry must contain an object or array.")

    @staticmethod
    def _count_nonempty_lines(path: Path) -> int:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())


class MetricsCollector:
    """Collect authoritative dashboard metrics from configured sources."""

    def __init__(
        self,
        paths: RuntimePaths,
        registry_counter: RegistryCounter | None = None,
    ) -> None:
        self._paths = paths
        self._counter = registry_counter or RegistryCounter()

    def collect(self) -> dict[str, ExecutiveMetric]:
        metrics: dict[str, ExecutiveMetric] = {}

        for specification in REGISTRY_SPECIFICATIONS:
            metrics[specification.metric_id] = self._registry_metric(
                specification
            )

        metrics["knowledge_files"] = self._knowledge_files_metric()
        metrics["project_files"] = self._project_files_metric()
        metrics["logical_cpus"] = self._logical_cpu_metric()

        return metrics

    def _registry_metric(
        self,
        specification: RegistrySpecification,
    ) -> ExecutiveMetric:
        configured_path = os.environ.get(specification.env_path)

        if not configured_path:
            return ExecutiveMetric(
                identifier=specification.metric_id,
                name=specification.name,
                value=None,
                state=MetricState.NOT_CONFIGURED,
                source=specification.env_path,
                description=specification.description,
            )

        path = Path(configured_path)
        table = (
            os.environ.get(specification.env_table)
            if specification.env_table
            else None
        )

        try:
            value = self._counter.count(path=path, table=table)
        except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            return ExecutiveMetric(
                identifier=specification.metric_id,
                name=specification.name,
                value=None,
                state=MetricState.UNAVAILABLE,
                source=str(path),
                description=(
                    f"{specification.description} Collection failed: {exc}"
                ),
            )

        return ExecutiveMetric(
            identifier=specification.metric_id,
            name=specification.name,
            value=value,
            state=MetricState.AVAILABLE,
            source=str(path),
            description=specification.description,
        )

    @staticmethod
    def _count_files(path: Path) -> int:
        return sum(1 for item in path.rglob("*") if item.is_file())

    def _knowledge_files_metric(self) -> ExecutiveMetric:
        if os.environ.get("JARVIS_DASHBOARD_RECURSIVE_INVENTORY", "").lower() not in {"1", "true", "yes"}:
            return ExecutiveMetric(
                identifier="knowledge_files",
                name="Knowledge Files",
                value=None,
                state=MetricState.NOT_CONFIGURED,
                source="JARVIS_DASHBOARD_RECURSIVE_INVENTORY",
                description="Recursive file inventory is disabled for dashboard refreshes.",
            )

        path = self._paths.knowledge_root

        if not path.is_dir():
            return ExecutiveMetric(
                identifier="knowledge_files",
                name="Knowledge Files",
                value=None,
                state=MetricState.UNAVAILABLE,
                source=str(path),
                description="Files currently present in the Knowledge root.",
            )

        try:
            value = self._count_files(path)
        except OSError as exc:
            return ExecutiveMetric(
                identifier="knowledge_files",
                name="Knowledge Files",
                value=None,
                state=MetricState.UNAVAILABLE,
                source=str(path),
                description=f"Knowledge inventory failed: {exc}",
            )

        return ExecutiveMetric(
            identifier="knowledge_files",
            name="Knowledge Files",
            value=value,
            state=MetricState.AVAILABLE,
            source=str(path),
            description="Files currently present in the Knowledge root.",
        )

    def _project_files_metric(self) -> ExecutiveMetric:
        if os.environ.get("JARVIS_DASHBOARD_RECURSIVE_INVENTORY", "").lower() not in {"1", "true", "yes"}:
            return ExecutiveMetric(
                identifier="project_files",
                name="Project Files",
                value=None,
                state=MetricState.NOT_CONFIGURED,
                source="JARVIS_DASHBOARD_RECURSIVE_INVENTORY",
                description="Recursive file inventory is disabled for dashboard refreshes.",
            )

        path = self._paths.project_root

        try:
            value = self._count_files(path)
        except OSError as exc:
            return ExecutiveMetric(
                identifier="project_files",
                name="Project Files",
                value=None,
                state=MetricState.UNAVAILABLE,
                source=str(path),
                description=f"Project inventory failed: {exc}",
            )

        return ExecutiveMetric(
            identifier="project_files",
            name="Project Files",
            value=value,
            state=MetricState.AVAILABLE,
            source=str(path),
            description="Files currently present in the JARVIS project.",
        )

    @staticmethod
    def _logical_cpu_metric() -> ExecutiveMetric:
        value = os.cpu_count()

        return ExecutiveMetric(
            identifier="logical_cpus",
            name="Logical CPUs",
            value=value,
            state=(
                MetricState.AVAILABLE
                if value is not None
                else MetricState.UNAVAILABLE
            ),
            source="os.cpu_count",
            description="Logical processors visible to the runtime.",
        )


def worst_health_state(states: Iterable[HealthState]) -> HealthState:
    """Return the most severe health state in an iterable."""

    severity = {
        HealthState.UNKNOWN: 0,
        HealthState.HEALTHY: 1,
        HealthState.UNAVAILABLE: 2,
        HealthState.DEGRADED: 3,
        HealthState.CRITICAL: 4,
    }

    values = tuple(states)
    if not values:
        return HealthState.UNKNOWN

    return max(values, key=lambda state: severity[state])
