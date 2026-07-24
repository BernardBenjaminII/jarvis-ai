from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.conversation import (
    CatalogGroundingService, ExecutiveConversationOrchestrator,
    ExecutiveConversationService,
)
from core.executive.director import ExecutiveDirector


class KnowledgeGroundingTests(unittest.TestCase):
    @staticmethod
    def rows(query: str, limit: int):
        if "unknown" in query.lower():
            return []
        return [{
            "subject": "linux.security",
            "confidence": 0.92,
            "assigned_by": "fixture",
            "file_path": "/knowledge/linux/security.pdf",
        }]

    def build(self, root: Path, capture: list[str] | None = None):
        grounding = CatalogGroundingService(
            database_path=root / "catalog.sqlite",
            search_handler=self.rows,
        )
        director = ExecutiveDirector(
            database_path=root / "missions.sqlite",
            knowledge_search=grounding.search_for_director,
        )
        def synthesize(prompt: str) -> str:
            if capture is not None:
                capture.append(prompt)
            return "grounded-answer"
        orchestrator = ExecutiveConversationOrchestrator(
            director=director,
            synthesis_handler=synthesize,
            grounding_service=grounding,
        )
        return ExecutiveConversationService(
            database_path=root / "conversation.sqlite",
            orchestrator=orchestrator,
        )

    def test_catalog_evidence_is_exposed_in_response_metadata(self):
        with TemporaryDirectory() as temp:
            response = self.build(Path(temp)).ask("Search Linux security")
            grounding = response.metadata["knowledge_grounding"]
            self.assertEqual(grounding["status"], "grounded")
            self.assertEqual(grounding["evidence_count"], 1)
            self.assertEqual(
                grounding["objectives"][0]["evidence"][0]["source_path"],
                "/knowledge/linux/security.pdf",
            )

    def test_missing_evidence_declares_a_knowledge_gap(self):
        with TemporaryDirectory() as temp:
            response = self.build(Path(temp)).ask("Unknown quantum archive")
            grounding = response.metadata["knowledge_grounding"]
            self.assertEqual(grounding["status"], "gap")
            self.assertEqual(grounding["gap_count"], 1)
            self.assertIn("acquisition", grounding["gaps"][0]["recommended_action"].lower())

    def test_synthesis_receives_evidence_and_gap_instructions(self):
        with TemporaryDirectory() as temp:
            captured: list[str] = []
            self.build(Path(temp), captured).ask("Search Linux security")
            self.assertIn("JARVIS KNOWLEDGE GROUNDING", captured[0])
            self.assertIn("/knowledge/linux/security.pdf", captured[0])
            self.assertIn("do not invent", captured[0].lower())

    def test_knowledge_director_executes_live_catalog_adapter(self):
        with TemporaryDirectory() as temp:
            response = self.build(Path(temp)).ask("Search the knowledge catalog for Linux")
            mission = response.metadata["missions"][0]
            knowledge_tasks = [task for task in mission["tasks"] if task["director"] == "knowledge"]
            self.assertTrue(knowledge_tasks)
            self.assertEqual(knowledge_tasks[0]["result"]["mode"], "catalog_grounding")
            self.assertEqual(knowledge_tasks[0]["result"]["status"], "grounded")

    def test_trace_records_grounding_lifecycle(self):
        with TemporaryDirectory() as temp:
            response = self.build(Path(temp)).ask("Search Linux security")
            stages = [event.stage for event in response.trace]
            self.assertIn("knowledge.grounding", stages)
            grounding_events = [event for event in response.trace if event.stage == "knowledge.grounding"]
            self.assertEqual(grounding_events[-1].data["evidence_count"], 1)


if __name__ == "__main__":
    unittest.main()
