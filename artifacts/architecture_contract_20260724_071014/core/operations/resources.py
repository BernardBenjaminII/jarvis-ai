"""Runtime resource collection for the Operations interface."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .contracts import ResourceProvider
from .models import Provenance, ResourceSnapshot, utc_now


class SystemResourceProvider:
    """Collects standard-library measurements, with optional psutil enrichment."""

    def __init__(self, disk_path: str | Path = "/") -> None:
        self._disk_path = Path(disk_path)

    def collect_resources(self) -> Mapping[str, Any]:
        disk = shutil.disk_usage(self._disk_path)
        disk_percent = (disk.used / disk.total * 100.0) if disk.total else None

        load_average = None
        if hasattr(os, "getloadavg"):
            load_average = float(os.getloadavg()[0])

        cpu_percent = None
        memory_percent = None
        try:
            import psutil  # type: ignore

            cpu_percent = float(psutil.cpu_percent(interval=None))
            memory_percent = float(psutil.virtual_memory().percent)
        except ImportError:
            pass

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "load_average_1m": load_average,
            "queue_depth": 0,
            "worker_count": 1,
        }


class ResourceCollector:
    """Converts a provider measurement into a stable resource snapshot."""

    def __init__(self, provider: ResourceProvider | None = None) -> None:
        self._provider = provider or SystemResourceProvider()

    def collect(
        self,
        *,
        mission_count: int,
        measured_at: datetime | None = None,
    ) -> ResourceSnapshot:
        now = measured_at or utc_now()
        result = self._provider.collect_resources()

        return ResourceSnapshot(
            cpu_percent=_optional_float(result.get("cpu_percent")),
            memory_percent=_optional_float(result.get("memory_percent")),
            disk_percent=_optional_float(result.get("disk_percent")),
            load_average_1m=_optional_float(result.get("load_average_1m")),
            queue_depth=int(result.get("queue_depth", 0)),
            mission_count=mission_count,
            worker_count=int(result.get("worker_count", 0)),
            measured_at=now,
            provenance=Provenance(
                source=type(self._provider).__name__,
                source_version="mc1001",
                captured_at=now,
            ),
        )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
