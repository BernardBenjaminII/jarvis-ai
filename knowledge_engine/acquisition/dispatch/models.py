"""
Immutable results for acquisition-to-assimilation dispatch.

These models contain no SQL and perform no Phase VI execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
)


@dataclass(frozen=True, slots=True)
class AssimilationDispatchResult:
    """Result of one bounded dispatcher invocation."""

    claimed: int
    dispatched: int
    failed: int
    skipped: int
    handoffs: tuple[AssimilationHandoffRecord, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("claimed", self.claimed),
            ("dispatched", self.dispatched),
            ("failed", self.failed),
            ("skipped", self.skipped),
        ):
            if value < 0:
                raise ValueError(
                    f"{name} must not be negative"
                )

        if (
            self.dispatched
            + self.failed
            + self.skipped
            != self.claimed
        ):
            raise ValueError(
                "dispatch outcome counts must equal claimed"
            )

        if len(self.handoffs) != self.claimed:
            raise ValueError(
                "handoff result count must equal claimed"
            )

    @property
    def succeeded(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "claimed": self.claimed,
            "dispatched": self.dispatched,
            "failed": self.failed,
            "skipped": self.skipped,
            "succeeded": self.succeeded,
            "handoffs": [
                handoff.to_dict()
                for handoff in self.handoffs
            ],
        }


__all__ = [
    "AssimilationDispatchResult",
]
