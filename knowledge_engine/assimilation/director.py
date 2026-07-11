"""
Mission-level coordination for JARVIS knowledge assimilation.

Phase VI-A2 establishes object-type-aware dispatch planning. Execution remains
locked until Phase VI-B supplies failure-safe handler contracts.
"""

from __future__ import annotations

from typing import Any, Sequence

from knowledge_engine.assimilation.mission import AssimilationMission
from knowledge_engine.assimilation.planner import AssimilationPlanner
from knowledge_engine.assimilation.runner import AssimilationRunner


class AssimilationExecutionLockedError(RuntimeError):
    """Raised when execution is attempted during the planning-only phase."""


class AssimilationDirector:
    """Coordinate inventory and object-type-aware assimilation planning."""

    def __init__(
        self,
        db: Any,
        *,
        runner: AssimilationRunner | None = None,
        planner: AssimilationPlanner | None = None,
    ):
        self.db = db
        self.runner = runner or AssimilationRunner(db)
        self.planner = planner or AssimilationPlanner(db)

    def inventory(self) -> list[dict[str, Any]]:
        """Return the current object and handler inventory."""

        return self.planner.inventory()

    def plan(
        self,
        *,
        limit: int = 25,
        object_types: Sequence[str] | None = None,
    ) -> AssimilationMission:
        """Create a read-only object-type-aware assimilation mission."""

        return self.planner.plan(
            limit=limit,
            object_types=object_types,
        )

    def execute(
        self,
        mission: AssimilationMission,
        *,
        stop_on_error: bool = True,
    ) -> AssimilationMission:
        """
        Refuse execution until Phase VI-B handler safety is implemented.

        Keeping the method present preserves the Director interface while
        preventing the current runner from processing validated queue objects
        with incompatible state assumptions.
        """

        del mission
        del stop_on_error

        raise AssimilationExecutionLockedError(
            "Assimilation execution is locked during Phase VI-A2. "
            "Use --plan or --inventory. Phase VI-B will introduce "
            "exception-safe handler execution, retries, recovery, and "
            "compatible state transitions."
        )

    def plan_and_execute(
        self,
        *,
        limit: int = 25,
        object_types: Sequence[str] | None = None,
        stop_on_error: bool = True,
    ) -> AssimilationMission:
        """Plan work and then invoke the guarded execution interface."""

        mission = self.plan(
            limit=limit,
            object_types=object_types,
        )

        return self.execute(
            mission,
            stop_on_error=stop_on_error,
        )
