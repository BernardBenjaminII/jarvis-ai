"""Tests for Phase V-C Query Understanding."""

from __future__ import annotations

import unittest

from knowledge_engine.query_understanding import (
    QueryAnalyzer,
    QueryUnderstandingService,
    understand_query,
)


class QueryAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = QueryAnalyzer()

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.analyzer.analyze("   ")

    def test_explanation_task_is_detected(self) -> None:
        result = self.analyzer.analyze(
            "Explain how SQLite indexes improve retrieval"
        )

        self.assertEqual(result.task, "explain")
        self.assertEqual(
            result.desired_output,
            "technical_explanation",
        )

    def test_database_and_retrieval_domains_are_detected(self) -> None:
        result = self.analyzer.analyze(
            "How do SQLite indexes improve semantic retrieval?"
        )

        self.assertIn("databases", result.domains)
        self.assertIn(
            "information_retrieval",
            result.domains,
        )

    def test_named_entities_are_extracted(self) -> None:
        result = self.analyzer.analyze(
            "Compare SQLite and PostgreSQL indexes"
        )

        lowered = {
            entity.lower()
            for entity in result.entities
        }

        self.assertIn("sqlite", lowered)
        self.assertIn("postgresql", lowered)

    def test_retrieval_query_removes_request_scaffolding(self) -> None:
        result = self.analyzer.analyze(
            "Please explain how SQLite indexes improve retrieval"
        )

        lowered = result.retrieval_query.lower()

        self.assertIn("sqlite", lowered)
        self.assertIn("indexes", lowered)
        self.assertIn("retrieval", lowered)
        self.assertNotIn("please", lowered)
        self.assertNotIn("explain", lowered)

    def test_specialists_follow_detected_domains(self) -> None:
        result = self.analyzer.analyze(
            "Explain SQLite vector retrieval"
        )

        self.assertIn(
            "database",
            result.specialists,
        )

        self.assertIn(
            "search_engine",
            result.specialists,
        )

    def test_unknown_domain_uses_general_specialist(self) -> None:
        result = self.analyzer.analyze(
            "Tell me about medieval poetry"
        )

        self.assertEqual(
            result.specialists,
            ("general_knowledge",),
        )

    def test_compare_task_is_detected(self) -> None:
        result = self.analyzer.analyze(
            "Compare Python and Java"
        )

        self.assertEqual(result.task, "compare")
        self.assertEqual(
            result.desired_output,
            "comparison",
        )

    def test_how_to_task_is_detected(self) -> None:
        result = self.analyzer.analyze(
            "How to configure Linux systemd services"
        )

        self.assertEqual(result.task, "how_to")
        self.assertEqual(
            result.desired_output,
            "step_by_step_instructions",
        )

    def test_analysis_is_serializable(self) -> None:
        result = self.analyzer.analyze(
            "Explain Python generators"
        )

        mapping = result.as_dict()

        self.assertEqual(
            mapping["task"],
            "explain",
        )
        self.assertIsInstance(
            mapping["domains"],
            list,
        )
        self.assertIsInstance(
            mapping["keywords"],
            list,
        )

    def test_confidence_increases_for_structured_query(self) -> None:
        structured = self.analyzer.analyze(
            "Explain how SQLite indexes improve retrieval"
        )

        vague = self.analyzer.analyze(
            "something interesting"
        )

        self.assertGreater(
            structured.confidence,
            vague.confidence,
        )


class QueryUnderstandingServiceTests(unittest.TestCase):
    def test_service_returns_analysis(self) -> None:
        result = QueryUnderstandingService().understand(
            "Explain Linux processes"
        )

        self.assertEqual(result.task, "explain")
        self.assertIn(
            "operating_systems",
            result.domains,
        )

    def test_convenience_function(self) -> None:
        result = understand_query(
            "Find Python documentation"
        )

        self.assertEqual(result.task, "locate")
        self.assertIn(
            "programming",
            result.domains,
        )


if __name__ == "__main__":
    unittest.main()
