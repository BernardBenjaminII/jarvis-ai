"""
Persistent mission models for controlled JARVIS knowledge assimilation.
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
    PAUSED = "paused"
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


TERMINAL_ITEM_STATUSES = {
    MissionItemStatus.COMPLETED,
    MissionItemStatus.SKIPPED,
    MissionItemStatus.FAILED,
    MissionItemStatus.BLOCKED,
}


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
    started_at: str | None = None
    completed_at: str | None = None

    @property
    def dispatchable(self) -> bool:
        return self.handler_readiness != "unsupported"

    @property
    def executable(self) -> bool:
        return (
            self.assimilation_state == "queued"
            and self.dispatchable
            and self.executable_in_current_phase
        )

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_ITEM_STATUSES

    def mark_processing(self) -> None:
        self.status = MissionItemStatus.PROCESSING
        self.started_at = utc_now()
        self.completed_at = None

    def mark_terminal(
        self,
        *,
        status: MissionItemStatus,
        message: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        if status not in TERMINAL_ITEM_STATUSES:
            raise ValueError(f"Non-terminal item status: {status.value}")

        self.status = status
        self.message = message
        self.result = result
        self.completed_at = utc_now()

    def reset_interrupted_processing(self) -> None:
        """
        Return an interrupted item checkpoint to queued.

        The document runner remains responsible for recovering any stale
        database-level processing claim.
        """

        if self.status == MissionItemStatus.PROCESSING:
            self.status = MissionItemStatus.QUEUED
            self.message = (
                "Mission item recovered from interrupted processing checkpoint."
            )
            self.started_at = None
            self.completed_at = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["dispatchable"] = self.dispatchable
        payload["executable"] = self.executable
        payload["terminal"] = self.terminal
        return payload

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "AssimilationMissionItem":
        return cls(
            sequence=int(payload["sequence"]),
            object_uuid=str(payload["object_uuid"]),
            object_path=str(payload["object_path"]),
            object_type=str(payload["object_type"]),
            lifecycle_state=str(payload["lifecycle_state"]),
            assimilation_state=str(payload["assimilation_state"]),
            updated_at=payload.get("updated_at"),
            handler_name=str(payload["handler_name"]),
            handler_kind=str(payload["handler_kind"]),
            handler_readiness=str(payload["handler_readiness"]),
            handler_description=str(payload["handler_description"]),
            executable_in_current_phase=bool(
                payload["executable_in_current_phase"]
            ),
            path_exists=bool(payload["path_exists"]),
            path_is_file=bool(payload["path_is_file"]),
            path_is_directory=bool(payload["path_is_directory"]),
            size_bytes=(
                int(payload["size_bytes"])
                if payload.get("size_bytes") is not None
                else None
            ),
            status=MissionItemStatus(
                payload.get("status", MissionItemStatus.QUEUED.value)
            ),
            message=payload.get("message"),
            result=payload.get("result"),
            started_at=payload.get("started_at"),
            completed_at=payload.get("completed_at"),
        )


@dataclass
class AssimilationMission:
    """A deterministic, persistent assimilation work plan."""

    mission_id: str
    created_at: str
    database_path: str
    requested_limit: int
    requested_object_types: list[str]
    status: MissionStatus
    items: list[AssimilationMissionItem] = field(default_factory=list)
    planning_notes: list[str] = field(default_factory=list)
    started_at: str | None = None
    paused_at: str | None = None
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
    def pending_items(self) -> list[AssimilationMissionItem]:
        return [
            item
            for item in self.items
            if item.status == MissionItemStatus.QUEUED
        ]

    @property
    def remaining_items(self) -> int:
        return len(self.pending_items)

    @property
    def terminal_items(self) -> int:
        return sum(item.terminal for item in self.items)

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
        if self.started_at is None:
            self.started_at = utc_now()

        self.status = MissionStatus.RUNNING
        self.paused_at = None
        self.completed_at = None

    def pause(self) -> None:
        self.status = MissionStatus.PAUSED
        self.paused_at = utc_now()
        self.completed_at = None

    def recalculate_counts(self) -> None:
        self.processed = sum(
            item.status == MissionItemStatus.COMPLETED
            for item in self.items
        )
        self.failed = sum(
            item.status == MissionItemStatus.FAILED
            for item in self.items
        )
        self.skipped = sum(
            item.status == MissionItemStatus.SKIPPED
            for item in self.items
        )
        self.blocked = sum(
            item.status == MissionItemStatus.BLOCKED
            for item in self.items
        )

    def recover_interrupted_items(self) -> int:
        recovered = 0

        for item in self.items:
            if item.status == MissionItemStatus.PROCESSING:
                item.reset_interrupted_processing()
                recovered += 1

        if recovered:
            self.planning_notes.append(
                f"Recovered {recovered} interrupted mission item(s)."
            )

        return recovered

    def finalize(self) -> None:
        self.recalculate_counts()
        self.completed_at = utc_now()
        self.paused_at = None

        if self.remaining_items:
            self.status = MissionStatus.PAUSED
            self.paused_at = utc_now()
            self.completed_at = None
        elif self.failed and self.processed == 0:
            self.status = MissionStatus.FAILED
        elif self.blocked and self.processed == 0:
            self.status = MissionStatus.BLOCKED
        elif self.failed or self.blocked or self.skipped:
            self.status = MissionStatus.PARTIAL
        else:
            self.status = MissionStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        self.recalculate_counts()

        return {
            "mission_id": self.mission_id,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "paused_at": self.paused_at,
            "completed_at": self.completed_at,
            "database_path": self.database_path,
            "requested_limit": self.requested_limit,
            "requested_object_types": list(self.requested_object_types),
            "status": self.status.value,
            "summary": {
                "total_items": self.total_items,
                "dispatchable_items": self.dispatchable_items,
                "executable_items": self.executable_items,
                "terminal_items": self.terminal_items,
                "remaining_items": self.remaining_items,
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

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "AssimilationMission":
        summary = payload.get("summary", {})

        mission = cls(
            mission_id=str(payload["mission_id"]),
            created_at=str(payload["created_at"]),
            database_path=str(payload["database_path"]),
            requested_limit=int(payload["requested_limit"]),
            requested_object_types=[
                str(value)
                for value in payload.get("requested_object_types", [])
            ],
            status=MissionStatus(payload["status"]),
            items=[
                AssimilationMissionItem.from_dict(item)
                for item in payload.get("items", [])
            ],
            planning_notes=[
                str(note)
                for note in payload.get("planning_notes", [])
            ],
            started_at=payload.get("started_at"),
            paused_at=payload.get("paused_at"),
            completed_at=payload.get("completed_at"),
            processed=int(summary.get("processed", 0)),
            failed=int(summary.get("failed", 0)),
            skipped=int(summary.get("skipped", 0)),
            blocked=int(summary.get("blocked", 0)),
        )

        mission.recalculate_counts()
        return mission

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_mission_id(
    database_path: str,
    object_uuids: Iterable[str],
) -> str:
    """
    Build a mission identifier from content and creation time.

    The content digest identifies the work selection. The timestamp suffix
    permits separate runs of the same plan to coexist in mission history.
    """

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

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    return f"assim-{timestamp}-{digest[:10]}"
