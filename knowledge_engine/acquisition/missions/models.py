"""
Immutable contracts for durable acquisition missions.

Phase VII-A5 groups provenance-backed intake results into persistent missions.
Mission execution and assimilation handoff are deferred to later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AcquisitionMissionState(str, Enum):
    """Canonical lifecycle states for an acquisition mission."""

    PLANNED = "planned"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"


class AcquisitionMissionItemState(str, Enum):
    """Canonical outcome states for one mission item."""

    ACCEPTED = "accepted"
    REVIEW = "review"
    IGNORED = "ignored"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AcquisitionMissionRecord:
    """Current durable state of one acquisition mission."""

    mission_id: str
    request_id: str
    provider_id: str
    mission_state: AcquisitionMissionState
    created_at: str
    updated_at: str
    item_count: int
    accepted_count: int
    review_count: int
    ignored_count: int
    rejected_count: int
    campaign_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("mission_id", self.mission_id),
            ("request_id", self.request_id),
            ("provider_id", self.provider_id),
            ("created_at", self.created_at),
            ("updated_at", self.updated_at),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        counts = (
            self.item_count,
            self.accepted_count,
            self.review_count,
            self.ignored_count,
            self.rejected_count,
        )

        if any(count < 0 for count in counts):
            raise ValueError(
                "mission counts must not be negative"
            )

        classified_count = (
            self.accepted_count
            + self.review_count
            + self.ignored_count
            + self.rejected_count
        )

        if classified_count != self.item_count:
            raise ValueError(
                "classified counts must equal item_count"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "mission_state": self.mission_state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "item_count": self.item_count,
            "accepted_count": self.accepted_count,
            "review_count": self.review_count,
            "ignored_count": self.ignored_count,
            "rejected_count": self.rejected_count,
            "campaign_id": self.campaign_id,
        }


@dataclass(frozen=True, slots=True)
class AcquisitionMissionItemRecord:
    """One durable candidate outcome within an acquisition mission."""

    item_id: int
    mission_id: str
    item_order: int
    candidate_id: str
    provider_id: str
    source_uri: str
    local_path: str
    checksum_sha256: str
    item_state: AcquisitionMissionItemState
    decision_fingerprint: str
    created_at: str

    def __post_init__(self) -> None:
        if self.item_id < 1:
            raise ValueError(
                "item_id must be at least 1"
            )

        if self.item_order < 0:
            raise ValueError(
                "item_order must not be negative"
            )

        for name, value in (
            ("mission_id", self.mission_id),
            ("candidate_id", self.candidate_id),
            ("provider_id", self.provider_id),
            ("source_uri", self.source_uri),
            ("local_path", self.local_path),
            ("checksum_sha256", self.checksum_sha256),
            (
                "decision_fingerprint",
                self.decision_fingerprint,
            ),
            ("created_at", self.created_at),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        for name, value in (
            ("candidate_id", self.candidate_id),
            ("checksum_sha256", self.checksum_sha256),
            (
                "decision_fingerprint",
                self.decision_fingerprint,
            ),
        ):
            if len(value) != 64:
                raise ValueError(
                    f"{name} must contain 64 hexadecimal characters"
                )

            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(
                    f"{name} must be hexadecimal"
                ) from exc


@dataclass(frozen=True, slots=True)
class AcquisitionMissionBuildResult:
    """Result of constructing or resolving one durable mission."""

    mission: AcquisitionMissionRecord
    items: tuple[AcquisitionMissionItemRecord, ...]
    created: bool

    def __post_init__(self) -> None:
        if len(self.items) != self.mission.item_count:
            raise ValueError(
                "mission item count does not match persisted items"
            )

        item_orders = tuple(
            item.item_order
            for item in self.items
        )

        if item_orders != tuple(
            range(len(self.items))
        ):
            raise ValueError(
                "mission items must use contiguous zero-based ordering"
            )

        if any(
            item.mission_id != self.mission.mission_id
            for item in self.items
        ):
            raise ValueError(
                "all mission items must belong to the mission"
            )


__all__ = [
    "AcquisitionMissionBuildResult",
    "AcquisitionMissionItemRecord",
    "AcquisitionMissionItemState",
    "AcquisitionMissionRecord",
    "AcquisitionMissionState",
]
