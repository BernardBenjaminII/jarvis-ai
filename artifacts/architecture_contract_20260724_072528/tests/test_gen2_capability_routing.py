"""Tests for Gen 2 Phase II-A capability-based routing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.executive.capabilities import DirectorReadiness
from core.executive.director import ExecutiveDirector
from core.executive.models import Mission, MissionTask, TaskExecutionResult
from core.executive.registry import DirectorRegistry


def successful_handler(mission: Mission, task: MissionTask) -> TaskExecutionResult:
    return TaskExecutionResult(
        success=True,
        output={"director": task.director, "action": task.action},
    )


class CapabilityRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "missions.sqlite3"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_registry_selects_best_capability_coverage(self) -> None:
        registry = DirectorRegistry()
        registry.register(
            "executive",
            successful_handler,
            capabilities={"general_reasoning"},
            priority=10,
        )
        registry.register(
            "basic_knowledge",
            successful_handler,
            capabilities={"knowledge_search"},
            priority=30,
        )
        registry.register(
            "knowledge",
            successful_handler,
            capabilities={"knowledge_search", "knowledge_retrieval"},
            priority=20,
        )

        decision = registry.select({"knowledge_search", "knowledge_retrieval"})

        self.assertEqual(decision.selected_director, "knowledge")
        self.assertEqual(
            set(decision.required_capabilities),
            {"knowledge_search", "knowledge_retrieval"},
        )
        self.assertGreater(decision.candidates[0].score, 0.9)

    def test_unavailable_director_is_not_selected(self) -> None:
        registry = DirectorRegistry()
        registry.register(
            "executive",
            successful_handler,
            capabilities={"general_reasoning"},
        )
        registry.register(
            "offline_knowledge",
            successful_handler,
            capabilities={"knowledge_search", "knowledge_retrieval"},
            readiness=DirectorReadiness.UNAVAILABLE,
        )
        registry.register(
            "degraded_knowledge",
            successful_handler,
            capabilities={"knowledge_search"},
            readiness=DirectorReadiness.DEGRADED,
        )

        decision = registry.select({"knowledge_search"})

        self.assertEqual(decision.selected_director, "degraded_knowledge")

    def test_planner_records_routing_evidence(self) -> None:
        director = ExecutiveDirector(database_path=self.database)
        mission = director.submit(
            "Search the knowledge catalog for mission architecture",
            execute=False,
        )

        knowledge_tasks = [
            task
            for task in mission.tasks
            if "knowledge_search" in task.required_capabilities
        ]
        self.assertEqual(len(knowledge_tasks), 1)
        task = knowledge_tasks[0]
        self.assertEqual(task.director, "knowledge")
        self.assertEqual(
            task.routing_evidence["selected_director"],
            "knowledge",
        )
        self.assertIn("candidates", task.routing_evidence)
        self.assertIn("reason", task.routing_evidence)

    def test_director_catalog_exposes_capabilities(self) -> None:
        director = ExecutiveDirector(database_path=self.database)
        catalog = {entry["name"]: entry for entry in director.director_catalog()}

        self.assertIn("executive", catalog)
        self.assertIn("knowledge", catalog)
        self.assertIn("system", catalog)
        self.assertIn("mission_synthesis", catalog["executive"]["capabilities"])
        self.assertEqual(catalog["knowledge"]["readiness"], "degraded")

    def test_live_knowledge_bridge_is_ready(self) -> None:
        def fake_search(objective: str, context: dict) -> dict:
            return {"objective": objective, "context": context}

        director = ExecutiveDirector(
            database_path=self.database,
            knowledge_search=fake_search,
        )

        catalog = {entry["name"]: entry for entry in director.director_catalog()}
        self.assertEqual(catalog["knowledge"]["readiness"], "ready")

        mission = director.submit("Research the mission engine")
        knowledge_task = next(
            task for task in mission.tasks if task.director == "knowledge"
        )
        self.assertEqual(
            knowledge_task.result["objective"],
            "Research the mission engine",
        )


if __name__ == "__main__":
    unittest.main()
