"""
Mission models for controlled JARVIS knowledge assimilation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


class MissionStatus(str, Enum):
    """Lifecycle states for an assimilation mission."""

    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class MissionItemStatus(str, Enum):
    """Execution states for an individual mission item."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AssimilationMissionItem:
    """One registry object selected for an assimilation mission."""

    sequence: int
    object_uuid: str
    object_path: str
    object_type: str
    lifecycle_state: str
    assimilation_state: str
    updated_at: str | None

    handler_name: str
    handler_kind: str
    handler_readiness: str
    handler_description: str
    executable_in_current_phase: bool

    path_exists: bool
    path_is_file: bool
    path_is_directory: bool
    size_bytes: int | None

    status: MissionItemStatus = MissionItemStatus.QUEUED
    message: str | None = None
    result: dict[str, Any] | None = None

    @property
    def dispatchable(self) -> bool:
        """Return whether the object has a known non-unsupported handler."""

        return self.handler_readiness != "unsupported"

    @property
    def executable(self) -> bool:
        """
        Return whether the item may execute in the current phase.

        Phase VI-A2 is a planning phase, so registered handlers remain
        non-executable until their safety and recovery contracts are complete.
        """

        return (
            self.assimilation_state == "queued"
            and self.dispatchable
            and self.executable_in_current_phase
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["dispatchable"] = self.dispatchable
        payload["executable"] = self.executable
        return payload


@dataclass
class AssimilationMission:
    """A deterministic, bounded assimilation work plan."""

    mission_id: str
    created_at: str
    database_path: str
    requested_limit: int
    requested_object_types: list[str]
    status: MissionStatus
    items: list[AssimilationMissionItem] = field(default_factory=list)
    planning_notes: list[str] = field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    blocked: int = 0

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def dispatchable_items(self) -> int:
        return sum(item.dispatchable for item in self.items)

    @property
    def executable_items(self) -> int:
        return sum(item.executable for item in self.items)

    @property
    def has_work(self) -> bool:
        return bool(self.items)

    @property
    def handler_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for item in self.items:
            counts[item.handler_name] = counts.get(item.handler_name, 0) + 1

        return dict(sorted(counts.items()))

    @property
    def object_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for item in self.items:
            counts[item.object_type] = counts.get(item.object_type, 0) + 1

        return dict(sorted(counts.items()))

    @property
    def fingerprint(self) -> str:
        """Return a stable fingerprint of the mission selection."""

        payload = {
            "database_path": self.database_path,
            "requested_limit": self.requested_limit,
            "requested_object_types": self.requested_object_types,
            "items": [
                {
                    "sequence": item.sequence,
                    "object_uuid": item.object_uuid,
                    "object_path": item.object_path,
                    "object_type": item.object_type,
                    "assimilation_state": item.assimilation_state,
                    "updated_at": item.updated_at,
                    "handler_name": item.handler_name,
                }
                for item in self.items
            ],
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def mark_started(self) -> None:
        self.status = MissionStatus.RUNNING
        self.started_at = utc_now()

    def finalize(self) -> None:
        self.completed_at = utc_now()

        if self.failed and self.processed == 0:
            self.status = MissionStatus.FAILED
        elif self.blocked and self.processed == 0:
            self.status = MissionStatus.BLOCKED
        elif self.failed or self.blocked or self.skipped:
            self.status = MissionStatus.PARTIAL
        else:
            self.status = MissionStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "database_path": self.database_path,
            "requested_limit": self.requested_limit,
            "requested_object_types": list(self.requested_object_types),
            "status": self.status.value,
            "summary": {
                "total_items": self.total_items,
                "dispatchable_items": self.dispatchable_items,
                "executable_items": self.executable_items,
                "processed": self.processed,
                "failed": self.failed,
                "skipped": self.skipped,
                "blocked": self.blocked,
                "object_type_counts": self.object_type_counts,
                "handler_counts": self.handler_counts,
            },
            "planning_notes": list(self.planning_notes),
            "items": [item.to_dict() for item in self.items],
        }

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination


def utc_now() -> str:
    """Return an RFC 3339-compatible UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def build_mission_id(
    database_path: str,
    object_uuids: Iterable[str],
) -> str:
    """Build a compact deterministic mission identifier."""

    payload = {
        "database_path": str(Path(database_path).expanduser().resolve()),
        "object_uuids": list(object_uuids),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return f"assim-{digest[:16]}"
