from __future__ import annotations

import unittest
from unittest.mock import patch

from core.conversation.grounded_answer.integration import (
    augment_synthesis_input,
    ensure_grounded_answer_service,
    get_last_grounded_answer_plan,
)
from core.retrieval.qualification import QualificationResult


class FakeContext:
    operator_input = "Unknown integration question"
    mode = "full"
    channel = "text"
    metadata = {"request_id": "request-1", "session_id": "session-1"}


class FakeOrchestrator:
    pass


class Tests(unittest.TestCase):
    def test_service_attached_once(self):
        orchestrator = FakeOrchestrator()
        first = ensure_grounded_answer_service(orchestrator)
        second = ensure_grounded_answer_service(orchestrator)
        self.assertIs(first, second)

    def test_no_result_preserves_prompt(self):
        orchestrator = FakeOrchestrator()
        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=None,
        ):
            result = augment_synthesis_input(
                orchestrator,
                FakeContext(),
                "Existing prompt",
            )
        self.assertEqual(result, "Existing prompt")

    def test_plan_contract_added(self):
        orchestrator = FakeOrchestrator()
        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=QualificationResult(),
        ):
            result = augment_synthesis_input(
                orchestrator,
                FakeContext(),
                "Existing prompt",
            )
        self.assertIn("JARVIS GROUNDED ANSWER CONTRACT:", result)
        self.assertIsNotNone(get_last_grounded_answer_plan(orchestrator))

    def test_original_prompt_preserved(self):
        orchestrator = FakeOrchestrator()
        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=QualificationResult(),
        ):
            result = augment_synthesis_input(
                orchestrator,
                FakeContext(),
                "ORIGINAL PROMPT MARKER",
            )
        self.assertIn("ORIGINAL PROMPT MARKER", result)

    def test_unknown_plan_has_action(self):
        orchestrator = FakeOrchestrator()
        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=QualificationResult(),
        ):
            augment_synthesis_input(orchestrator, FakeContext(), "Prompt")
        plan = get_last_grounded_answer_plan(orchestrator)
        self.assertEqual(plan.state.value, "unknown")
        self.assertTrue(plan.recommended_action)


if __name__ == "__main__":
    unittest.main()
