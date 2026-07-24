"""Canonical Executive Projection Bus."""
from __future__ import annotations
import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from core.integration.readiness import ExecutiveReadiness, ReadinessColor, ReadinessLevel, normalize_projection_readiness

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _as_mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise TypeError("Projection payload must be a mapping.")
    return value

@dataclass(frozen=True)
class ProjectionBusSnapshot:
    schema_version: str
    generated_at: datetime
    revision: int
    overall: ExecutiveReadiness
    readiness: tuple[ExecutiveReadiness, ...]
    projections: Mapping[str, Mapping[str, Any]]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": iso_z(self.generated_at),
            "revision": self.revision,
            "overall": self.overall.to_dict(),
            "readiness": {item.capability_id: item.to_dict() for item in self.readiness},
            "projections": {key: dict(value) for key, value in sorted(self.projections.items())},
            "fingerprint": self.fingerprint,
        }

class ExecutiveProjectionBus:
    SCHEMA_VERSION = "1.0"
    def __init__(self, projection_service: Any) -> None:
        self.projection_service = projection_service
        self._lock = threading.RLock()
        self._revision = 0
        self._last_fingerprint: str | None = None
        self._last_snapshot: ProjectionBusSnapshot | None = None

    def _collect_projections(self) -> dict[str, Mapping[str, Any]]:
        raw = _as_mapping(self.projection_service.all_projections())
        projections = _as_mapping(raw.get("projections", raw))
        result: dict[str, Mapping[str, Any]] = {}
        for key, value in projections.items():
            try:
                result[str(key)] = _as_mapping(value)
            except TypeError:
                continue
        return dict(sorted(result.items()))

    @staticmethod
    def _fingerprint_payload(projections, readiness) -> str:
        payload = {
            "projections": projections,
            "readiness": [{
                "capability_id": item.capability_id,
                "level": item.level.value,
                "color": item.color.value,
                "ready": item.ready,
                "source_status": item.source_status,
            } for item in readiness],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _overall(readiness):
        checked_at = utc_now()
        if not readiness:
            return ExecutiveReadiness("system", "JARVIS", ReadinessLevel.BAD, ReadinessColor.RED, False,
                "No executive projections are registered.", "not_configured", checked_at, {"projection_count": 0})
        bad = [x for x in readiness if x.level is ReadinessLevel.BAD]
        caution = [x for x in readiness if x.level is ReadinessLevel.CAUTION]
        if bad:
            level, color, ready = ReadinessLevel.BAD, ReadinessColor.RED, False
            summary = f"{len(bad)} executive capability projection(s) are unavailable."
        elif caution:
            level, color, ready = ReadinessLevel.CAUTION, ReadinessColor.YELLOW, True
            summary = f"{len(caution)} executive capability projection(s) require caution."
        else:
            level, color, ready = ReadinessLevel.GOOD, ReadinessColor.GREEN, True
            summary = "All registered executive capability projections are ready."
        return ExecutiveReadiness("system", "JARVIS", level, color, ready, summary, level.value, checked_at,
            {"projection_count": len(readiness), "good": sum(x.level is ReadinessLevel.GOOD for x in readiness),
             "caution": len(caution), "bad": len(bad)})

    def snapshot(self, *, force: bool = False) -> ProjectionBusSnapshot:
        with self._lock:
            projections = self._collect_projections()
            readiness = tuple(normalize_projection_readiness(k, v) for k, v in projections.items())
            fingerprint = self._fingerprint_payload(projections, readiness)
            if not force and self._last_snapshot is not None and fingerprint == self._last_fingerprint:
                return self._last_snapshot
            if fingerprint != self._last_fingerprint:
                self._revision += 1
            snapshot = ProjectionBusSnapshot(self.SCHEMA_VERSION, utc_now(), self._revision,
                self._overall(readiness), readiness, projections, fingerprint)
            self._last_fingerprint = fingerprint
            self._last_snapshot = snapshot
            return snapshot

    def readiness(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {"schema_version": snapshot.schema_version, "generated_at": iso_z(snapshot.generated_at),
            "revision": snapshot.revision, "overall": snapshot.overall.to_dict(),
            "capabilities": {x.capability_id: x.to_dict() for x in snapshot.readiness},
            "fingerprint": snapshot.fingerprint}

    def projection(self, projection_id: str):
        return self.snapshot().projections.get(projection_id)

    def manifest(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {"schema_version": snapshot.schema_version, "generated_at": iso_z(snapshot.generated_at),
            "revision": snapshot.revision, "projection_count": len(snapshot.projections),
            "projection_ids": sorted(snapshot.projections),
            "readiness_endpoint": "/operations/bridge/readiness",
            "snapshot_endpoint": "/operations/bridge",
            "projection_endpoint_template": "/operations/bridge/projections/{projection_id}",
            "fingerprint": snapshot.fingerprint}

_default_bus = None
_default_bus_lock = threading.RLock()

def get_default_projection_bus() -> ExecutiveProjectionBus:
    global _default_bus
    with _default_bus_lock:
        if _default_bus is None:
            from core.integration.bootstrap import get_default_integration_runtime
            _default_bus = ExecutiveProjectionBus(get_default_integration_runtime().projection_service)
        return _default_bus

def reset_default_projection_bus() -> None:
    global _default_bus
    with _default_bus_lock:
        _default_bus = None
