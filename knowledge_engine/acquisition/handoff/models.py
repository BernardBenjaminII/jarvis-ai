"""
Immutable contracts for controlled acquisition-to-assimilation handoff.

A handoff request represents accepted acquisition work that is ready to be
dispatched through the canonical Phase VI assimilation interfaces.

This module contains no SQL and performs no assimilation execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AssimilationHandoffState(str, Enum):
    """Canonical lifecycle states for an assimilation handoff."""

    QUEUED = "queued"
    DISPATCHING = "dispatching"
    DISPATCHED = "dispatched"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class AssimilationHandoffRecord:
    """Current durable state of one assimilation handoff request."""

    handoff_id: str
    mission_id: str
    mission_item_id: int
    candidate_id: str
    provider_id: str
    source_uri: str
    local_path: str
    checksum_sha256: str
    decision_fingerprint: str
    handoff_state: AssimilationHandoffState
    created_at: str
    updated_at: str
    dispatch_attempt_count: int
    assimilation_reference: str | None = None
    last_error: str | None = None

    def __post_init__(self) -> None:
        if self.mission_item_id < 1:
            raise ValueError(
                "mission_item_id must be at least 1"
            )

        if self.dispatch_attempt_count < 0:
            raise ValueError(
                "dispatch_attempt_count must not be negative"
            )

        for name, value in (
            ("handoff_id", self.handoff_id),
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
            ("updated_at", self.updated_at),
        ):
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )

        for name, value in (
            ("handoff_id", self.handoff_id),
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "mission_id": self.mission_id,
            "mission_item_id": self.mission_item_id,
            "candidate_id": self.candidate_id,
            "provider_id": self.provider_id,
            "source_uri": self.source_uri,
            "local_path": self.local_path,
            "checksum_sha256": self.checksum_sha256,
            "decision_fingerprint": (
                self.decision_fingerprint
            ),
            "handoff_state": self.handoff_state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dispatch_attempt_count": (
                self.dispatch_attempt_count
            ),
            "assimilation_reference": (
                self.assimilation_reference
            ),
            "last_error": self.last_error,
        }


@dataclass(frozen=True, slots=True)
class AssimilationHandoffBuildResult:
    """Result of preparing one acquisition mission for assimilation."""

    mission_id: str
    handoffs: tuple[AssimilationHandoffRecord, ...]
    created_count: int
    existing_count: int
    excluded_count: int

    def __post_init__(self) -> None:
        if not self.mission_id.strip():
            raise ValueError(
                "mission_id must not be empty"
            )

        for name, value in (
            ("created_count", self.created_count),
            ("existing_count", self.existing_count),
            ("excluded_count", self.excluded_count),
        ):
            if value < 0:
                raise ValueError(
                    f"{name} must not be negative"
                )

        if (
            self.created_count
            + self.existing_count
            != len(self.handoffs)
        ):
            raise ValueError(
                "created and existing counts must equal handoff count"
            )

        item_ids = tuple(
            handoff.mission_item_id
            for handoff in self.handoffs
        )

        if item_ids != tuple(sorted(item_ids)):
            raise ValueError(
                "handoffs must be ordered by mission_item_id"
            )

        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "handoff mission-item IDs must be unique"
            )

    @property
    def handoff_count(self) -> int:
        return len(self.handoffs)


__all__ = [
    "AssimilationHandoffBuildResult",
    "AssimilationHandoffRecord",
    "AssimilationHandoffState",
]
