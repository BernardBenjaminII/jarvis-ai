"""Mission snapshot adapter."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from .contracts import MissionProvider
from .enums import ActivityState, MissionState, ObjectiveState
from .models import (
    ActivitySnapshot,
    MissionSnapshot,
    ObjectiveSnapshot,
    Provenance,
    utc_now,
)


class EmptyMissionProvider:
    """Default provider used until an Executive adapter is registered."""

    def list_missions(self) -> Iterable[Mapping[str, Any]]:
        return ()


def _timestamp(value: Any, fallback: datetime) -> datetime:
    return value if isinstance(value, datetime) else fallback


class MissionSnapshotAdapter:
    """Converts provider mappings into immutable mission snapshots."""

    def __init__(self, provider: MissionProvider | None = None) -> None:
        self._provider = provider or EmptyMissionProvider()

    def collect(self, *, captured_at: datetime | None = None) -> tuple[MissionSnapshot, ...]:
        now = captured_at or utc_now()
        snapshots: list[MissionSnapshot] = []

        for record in self._provider.list_missions():
            mission_id = str(record.get("mission_id", record.get("id", ""))).strip()
            if not mission_id:
                continue

            provenance = Provenance(
                source=str(record.get("source", "executive")),
                source_version=str(record.get("source_version", "unknown")),
                captured_at=now,
            )

            objectives: list[ObjectiveSnapshot] = []
            for objective in record.get("objectives", ()):
                activities = tuple(
                    ActivitySnapshot(
                        activity_id=str(activity.get("activity_id", activity.get("id", ""))),
                        name=str(activity.get("name", "Unnamed activity")),
                        state=ActivityState(str(activity.get("state", "queued"))),
                        updated_at=_timestamp(activity.get("updated_at"), now),
                        provenance=provenance,
                    )
                    for activity in objective.get("activities", ())
                )
                objectives.append(
                    ObjectiveSnapshot(
                        objective_id=str(
                            objective.get("objective_id", objective.get("id", ""))
                        ),
                        name=str(objective.get("name", "Unnamed objective")),
                        state=ObjectiveState(str(objective.get("state", "pending"))),
                        activities=activities,
                        updated_at=_timestamp(objective.get("updated_at"), now),
                        provenance=provenance,
                    )
                )

            snapshots.append(
                MissionSnapshot(
                    mission_id=mission_id,
                    name=str(record.get("name", "Unnamed mission")),
                    state=MissionState(str(record.get("state", "planned"))),
                    objectives=tuple(objectives),
                    created_at=_timestamp(record.get("created_at"), now),
                    updated_at=_timestamp(record.get("updated_at"), now),
                    provenance=provenance,
                )
            )

        return tuple(sorted(snapshots, key=lambda item: item.mission_id))
