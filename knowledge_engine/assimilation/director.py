"""
Mission-level coordination and persistent recovery for JARVIS assimilation.

Phase VI-C provides:

- durable mission creation
- per-item checkpoints
- bounded execution
- pause and resume
- interrupted mission-item recovery
"""

from __future__ import annotations

from typing import Any, Sequence

from knowledge_engine.assimilation.mission import (
    AssimilationMission,
    MissionItemStatus,
    MissionStatus,
)
from knowledge_engine.assimilation.mission_store import (
    AssimilationMissionStore,
)
from knowledge_engine.assimilation.planner import AssimilationPlanner
from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.assimilation.registry_builder import (
    build_handler_registry,
)

class AssimilationExecutionLockedError(RuntimeError):
    """Raised when a mission contains no safely executable handler."""


class AssimilationDirector:
    """Coordinate persistent assimilation mission execution."""

    def __init__(
        self,
        db: Any,
        *,
        runner: AssimilationRunner | None = None,
        planner: AssimilationPlanner | None = None,
        mission_store: AssimilationMissionStore | None = None,
    ):
        self.db = db
        self.runner = runner or AssimilationRunner(db)
        self.planner = planner or AssimilationPlanner(db)
        self.mission_store = mission_store or AssimilationMissionStore(db)
        self.handler_registry = build_handler_registry(
            self.runner,
        )

    def inventory(self) -> list[dict[str, Any]]:
        return self.planner.inventory()

    def plan(
        self,
        *,
        limit: int = 25,
        object_types: Sequence[str] | None = None,
        persist: bool = True,
    ) -> AssimilationMission:
        mission = self.planner.plan(
            limit=limit,
            object_types=object_types,
        )

        if persist:
            self.mission_store.save_new(mission)

        return mission

    def load_mission(self, mission_id: str) -> AssimilationMission:
        return self.mission_store.load(mission_id)

    def history(
        self,
        *,
        limit: int = 25,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.mission_store.history(
            limit=limit,
            status=status,
        )

    def execute(
        self,
        mission: AssimilationMission,
        *,
        stop_on_error: bool = True,
        max_items: int | None = None,
    ) -> AssimilationMission:
        """
        Execute queued mission items with a checkpoint before and after each.

        max_items limits the number of queued items attempted in this call.
        Remaining queued items cause the mission to enter paused state.
        """

        if max_items is not None and max_items < 1:
            raise ValueError("max_items must be at least 1")

        if mission.status not in {
            MissionStatus.PLANNED,
            MissionStatus.PAUSED,
            MissionStatus.RUNNING,
        }:
            raise ValueError(
                "Only planned, paused, or interrupted running missions "
                "may execute"
            )

        mission.recover_interrupted_items()

        if not mission.items:
            mission.mark_started()
            mission.finalize()
            self.mission_store.checkpoint(mission)
            return mission

        if not any(
            item.executable
            for item in mission.pending_items
        ):
            if mission.remaining_items:
                raise AssimilationExecutionLockedError(
                    "The mission has remaining items, but none use an "
                    "executable Phase VI-C handler."
                )

            mission.finalize()
            self.mission_store.checkpoint(mission)
            return mission

        mission.mark_started()
        self.mission_store.checkpoint(mission)

        attempted_this_run = 0

        for item in mission.items:
            if item.status != MissionItemStatus.QUEUED:
                continue

            if max_items is not None and attempted_this_run >= max_items:
                mission.pause()
                self.mission_store.checkpoint(mission)
                return mission

            attempted_this_run += 1

            if not item.executable:
                item.mark_terminal(
                    status=MissionItemStatus.SKIPPED,
                    message=(
                        f"Handler {item.handler_name!r} is not executable "
                        "in Phase VI-C."
                    ),
                )
                mission.recalculate_counts()
                self.mission_store.checkpoint(
                    mission,
                    item=item,
                )
                continue

            try:
                handler = self.handler_registry.get(
                    item.object_type,
                )
            except LookupError:
                item.mark_terminal(
                    status=MissionItemStatus.BLOCKED,
                    message=(
                        f"No handler registered for "
                        f"{item.object_type!r}."
                    ),
                )

                mission.recalculate_counts()

                self.mission_store.checkpoint(
                    mission,
                    item=item,
                )

                if stop_on_error:
                    break

                continue


            item.mark_processing()
            self.mission_store.checkpoint(
                mission,
                item=item,
            )

            try:
                result = handler.execute(
                    object_uuid=item.object_uuid,
                )

            except Exception as exc:
                item.mark_terminal(
                    status=MissionItemStatus.FAILED,
                    message=f"{type(exc).__name__}: {exc}",
                    result={
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    },
                )
                mission.recalculate_counts()
                self.mission_store.checkpoint(
                    mission,
                    item=item,
                    last_error=item.message,
                )

                if stop_on_error:
                    break

                continue

            if int(result.get("processed", 0)) == 1:
                returned_uuid = result.get("object_uuid")

                if returned_uuid != item.object_uuid:
                    item.mark_terminal(
                        status=MissionItemStatus.BLOCKED,
                        message=(
                            "Runner returned a different object UUID than "
                            "the persistent mission checkpoint."
                        ),
                        result=dict(result),
                    )
                else:
                    item.mark_terminal(
                        status=MissionItemStatus.COMPLETED,
                        message="Document assimilation completed.",
                        result=dict(result),
                    )

            elif int(result.get("failed", 0)) == 1:
                item.mark_terminal(
                    status=MissionItemStatus.FAILED,
                    message=str(
                        result.get("error")
                        or result.get("message")
                        or "Document assimilation failed."
                    ),
                    result=dict(result),
                )

            else:
                item.mark_terminal(
                    status=MissionItemStatus.BLOCKED,
                    message=str(
                        result.get("message")
                        or "Runner did not claim the persistent mission item."
                    ),
                    result=dict(result),
                )

            mission.recalculate_counts()
            self.mission_store.checkpoint(
                mission,
                item=item,
                last_error=(
                    item.message
                    if item.status in {
                        MissionItemStatus.FAILED,
                        MissionItemStatus.BLOCKED,
                    }
                    else None
                ),
            )

            if (
                stop_on_error
                and item.status in {
                    MissionItemStatus.FAILED,
                    MissionItemStatus.BLOCKED,
                }
            ):
                break

        mission.finalize()
        self.mission_store.checkpoint(mission)
        return mission

    def resume(
        self,
        mission_id: str,
        *,
        stop_on_error: bool = True,
        max_items: int | None = None,
        recover_stale_minutes: int = 30,
    ) -> AssimilationMission:
        """
        Load and resume a persistent mission.

        Database-level stale document claims are recovered before mission-item
        checkpoints are replayed.
        """

        if recover_stale_minutes < 1:
            raise ValueError("recover_stale_minutes must be at least 1")

        mission = self.load_mission(mission_id)

        self.runner.recover_stale_processing(
            stale_after_minutes=recover_stale_minutes,
        )

        recovered = mission.recover_interrupted_items()

        if recovered:
            self.mission_store.checkpoint(mission)

        return self.execute(
            mission,
            stop_on_error=stop_on_error,
            max_items=max_items,
        )

    def plan_and_execute(
        self,
        *,
        limit: int = 25,
        object_types: Sequence[str] | None = None,
        stop_on_error: bool = True,
        max_items: int | None = None,
    ) -> AssimilationMission:
        mission = self.plan(
            limit=limit,
            object_types=object_types,
            persist=True,
        )

        return self.execute(
            mission,
            stop_on_error=stop_on_error,
            max_items=max_items,
        )
