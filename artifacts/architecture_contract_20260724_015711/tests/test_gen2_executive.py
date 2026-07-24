"""Tests for JARVIS Gen 2 Phase I."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.executive.contracts import InvalidMissionPlanError
from core.executive.director import ExecutiveDirector
from core.executive.engine import MissionEngine
from core.executive.models import (
    Mission,
    MissionStatus,
    MissionTask,
    TaskExecutionResult,
    TaskStatus,
)
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class ExecutiveDirectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "missions.sqlite3"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_general_mission_completes(self) -> None:
        director = ExecutiveDirector(database_path=self.database)

        mission = director.submit("Draft a project execution strategy")

        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        self.assertEqual(len(mission.tasks), 3)
        self.assertTrue(
            all(task.status == TaskStatus.COMPLETED for task in mission.tasks)
        )
        self.assertIsNotNone(mission.summary)

    def test_knowledge_mission_routes_to_knowledge_director(self) -> None:
        calls: list[tuple[str, dict]] = []

        def fake_search(objective: str, context: dict) -> dict:
            calls.append((objective, context))
            return {"matches": 3, "source": "fake-knowledge-director"}

        director = ExecutiveDirector(
            database_path=self.database,
            knowledge_search=fake_search,
        )

        mission = director.submit(
            "Search the knowledge catalog for Linux networking",
            context={"limit": 3},
        )

        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        self.assertEqual(len(calls), 1)
        knowledge_tasks = [
            task for task in mission.tasks if task.director == "knowledge"
        ]
        self.assertEqual(len(knowledge_tasks), 1)
        self.assertEqual(
            knowledge_tasks[0].result,
            {"matches": 3, "source": "fake-knowledge-director"},
        )

    def test_mission_persists_and_reloads(self) -> None:
        director = ExecutiveDirector(database_path=self.database)
        mission = director.submit("Explain the current knowledge architecture")

        reloaded = director.get_mission(mission.mission_id)

        self.assertEqual(reloaded.mission_id, mission.mission_id)
        self.assertEqual(reloaded.status, MissionStatus.COMPLETED)
        self.assertEqual(len(reloaded.tasks), len(mission.tasks))
        self.assertGreaterEqual(
            len(director.mission_events(mission.mission_id)),
            4,
        )

    def test_failed_director_blocks_dependent_synthesis(self) -> None:
        registry = DirectorRegistry()

        def good_handler(
            mission: Mission,
            task: MissionTask,
        ) -> TaskExecutionResult:
            return TaskExecutionResult(success=True, output={"ok": True})

        def bad_handler(
            mission: Mission,
            task: MissionTask,
        ) -> TaskExecutionResult:
            return TaskExecutionResult(success=False, error="controlled failure")

        registry.register("executive", good_handler)
        registry.register("failure", bad_handler)

        store = MissionStore(self.database)
        engine = MissionEngine(registry, store)

        first = MissionTask(
            title="Fail",
            director="failure",
            action="fail",
        )
        second = MissionTask(
            title="Blocked",
            director="executive",
            action="synthesize",
            depends_on=[first.task_id],
        )
        mission = Mission(
            objective="Test controlled failure",
            status=MissionStatus.PLANNED,
            tasks=[first, second],
        )
        store.save(mission)

        result = engine.execute(mission)

        self.assertEqual(result.status, MissionStatus.FAILED)
        self.assertEqual(first.status, TaskStatus.FAILED)
        self.assertEqual(second.status, TaskStatus.BLOCKED)

    def test_cycle_is_rejected(self) -> None:
        registry = DirectorRegistry()
        registry.register(
            "executive",
            lambda mission, task: TaskExecutionResult(success=True),
        )
        store = MissionStore(self.database)
        engine = MissionEngine(registry, store)

        first = MissionTask(
            title="First",
            director="executive",
            action="one",
        )
        second = MissionTask(
            title="Second",
            director="executive",
            action="two",
        )
        first.depends_on = [second.task_id]
        second.depends_on = [first.task_id]

        mission = Mission(
            objective="Cycle test",
            status=MissionStatus.PLANNED,
            tasks=[first, second],
        )

        with self.assertRaises(InvalidMissionPlanError):
            engine.execute(mission)


if __name__ == "__main__":
    unittest.main()
