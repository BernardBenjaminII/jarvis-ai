from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.conversation import ExecutiveConversationOrchestrator, ExecutiveConversationService
from core.executive.director import ExecutiveDirector


class DirectorActivationTests(unittest.TestCase):
    def build_service(self, root: Path) -> ExecutiveConversationService:
        director = ExecutiveDirector(database_path=root / "missions.sqlite")
        orchestrator = ExecutiveConversationOrchestrator(
            director=director,
            synthesis_handler=lambda question: f"SYNTHESIZED: {question}",
        )
        return ExecutiveConversationService(
            database_path=root / "conversation.sqlite",
            orchestrator=orchestrator,
        )

    def test_general_question_activates_executive_director(self):
        with TemporaryDirectory() as temp:
            response = self.build_service(Path(temp)).ask("Evaluate this situation")
            self.assertEqual(response.state.value, "completed")
            self.assertIn("executive", response.metadata["directors_activated"])
            self.assertEqual(len(response.metadata["missions"]), 1)
            self.assertEqual(response.metadata["missions"][0]["status"], "completed")

    def test_compound_request_creates_one_mission_per_objective(self):
        with TemporaryDirectory() as temp:
            response = self.build_service(Path(temp)).ask(
                "Search the catalog; then assess my Ubuntu system."
            )
            self.assertGreaterEqual(len(response.objectives), 2)
            self.assertEqual(len(response.metadata["missions"]), len(response.objectives))
            self.assertIn("knowledge", response.metadata["directors_activated"])
            self.assertIn("system", response.metadata["directors_activated"])

    def test_assignment_exposes_routing_evidence_and_task_results(self):
        with TemporaryDirectory() as temp:
            response = self.build_service(Path(temp)).ask("Search the knowledge catalog")
            mission = response.metadata["missions"][0]
            self.assertTrue(mission["tasks"])
            delegated = [task for task in mission["tasks"] if task["action"] == "search"]
            self.assertEqual(len(delegated), 1)
            self.assertEqual(delegated[0]["director"], "knowledge")
            self.assertIn("routing_evidence", delegated[0])
            self.assertIsNotNone(delegated[0]["result"])

    def test_trace_records_director_mission_lifecycle(self):
        with TemporaryDirectory() as temp:
            response = self.build_service(Path(temp)).ask("Create a general recommendation")
            stages = [event.stage for event in response.trace]
            self.assertIn("director.mission.created", stages)
            self.assertIn("director.mission.completed", stages)
            self.assertIn("executive.synthesis", stages)


if __name__ == "__main__":
    unittest.main()
