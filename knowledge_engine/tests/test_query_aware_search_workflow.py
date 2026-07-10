"""Integration tests for the Phase V-C Search workflow."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from knowledge_engine.director.workflows.search import SearchWorkflow


class QueryAwareSearchWorkflowTests(unittest.TestCase):

    def setUp(self) -> None:
        self.workflow = SearchWorkflow()

    def test_empty_query_is_rejected(self) -> None:

        request = SimpleNamespace(
            intent="search",
            query="   ",
            metadata={},
        )

        response = self.workflow.run(request)

        self.assertFalse(response.passed)
        self.assertEqual(
            response.message,
            "Missing query.",
        )

    @patch(
        "knowledge_engine.director.workflows.search.SearchService"
    )
    @patch(
        "knowledge_engine.director.workflows.search.KnowledgeDatabase"
    )
    def test_query_understanding_is_used(
        self,
        database_class,
        search_service_class,
    ) -> None:

        del database_class

        search_service_class.return_value.execute.return_value = Mock(
            passed=True,
            message="0 ranked results returned.",
            query="SQLite indexes retrieval",
            results=[],
            average_quality=100,
        )

        request = SimpleNamespace(
            intent="search",
            query="Please explain how SQLite indexes improve retrieval",
            metadata={"limit": 5},
        )

        response = self.workflow.run(request)

        self.assertTrue(response.passed)

        execute_call = (
            search_service_class.return_value.execute.call_args
        )

        retrieval_query = execute_call.kwargs["query"]

        self.assertIn("SQLite", retrieval_query)
        self.assertIn("indexes", retrieval_query)

        self.assertNotIn(
            "Please",
            retrieval_query,
        )

        self.assertNotIn(
            "explain",
            retrieval_query.lower(),
        )

        self.assertIn(
            "query_understanding",
            response.metadata,
        )

    @patch(
        "knowledge_engine.director.workflows.search.SearchService"
    )
    @patch(
        "knowledge_engine.director.workflows.search.KnowledgeDatabase"
    )
    def test_original_query_is_preserved(
        self,
        database_class,
        search_service_class,
    ) -> None:

        del database_class

        search_service_class.return_value.execute.return_value = Mock(
            passed=True,
            message="0 ranked results returned.",
            query="SQLite",
            results=[],
            average_quality=100,
        )

        original = "Explain SQLite indexes"

        request = SimpleNamespace(
            intent="search",
            query=original,
            metadata={"limit": 3},
        )

        response = self.workflow.run(request)

        self.assertEqual(
            response.metadata["original_query"],
            original,
        )

        self.assertIn(
            "retrieval_query",
            response.metadata,
        )


if __name__ == "__main__":
    unittest.main()
