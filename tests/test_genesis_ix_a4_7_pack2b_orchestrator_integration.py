from __future__ import annotations

import unittest
from unittest.mock import patch

from core.conversation.grounded_answer.integration import (
    augment_synthesis_input,
    ensure_grounded_answer_service,
    get_last_grounded_answer_plan,
    get_last_grounded_answer_response,
)
from core.retrieval.qualification import (
    QualificationResult,
)


class FakeContext:
    operator_input = "Unknown integration question"
    mode = "full"
    channel = "text"
    metadata = {
        "request_id": "request-1",
        "session_id": "session-1",
    }


class FakeOrchestrator:
    pass


class GenesisIXA47Pack2BTests(unittest.TestCase):
    def test_service_is_attached_once(self) -> None:
        orchestrator = FakeOrchestrator()

        first = ensure_grounded_answer_service(
            orchestrator
        )
        second = ensure_grounded_answer_service(
            orchestrator
        )

        self.assertIs(
            first,
            second,
        )
        self.assertIs(
            first,
            orchestrator.grounded_answer_service,
        )

    def test_absent_qualification_preserves_prompt(self) -> None:
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

        self.assertEqual(
            result,
            "Existing prompt",
        )
        self.assertIsNone(
            get_last_grounded_answer_plan(
                orchestrator
            )
        )

    def test_plan_is_built_once(self) -> None:
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

        self.assertIn(
            "JARVIS GROUNDED ANSWER CONTRACT:",
            result,
        )
        self.assertIsNotNone(
            get_last_grounded_answer_plan(
                orchestrator
            )
        )
        self.assertIsNotNone(
            get_last_grounded_answer_response(
                orchestrator
            )
        )

    def test_duplicate_contract_is_not_added(self) -> None:
        orchestrator = FakeOrchestrator()

        original = (
            "Existing prompt\n\n"
            "JARVIS GROUNDED ANSWER CONTRACT:\n"
        )

        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=QualificationResult(),
        ):
            result = augment_synthesis_input(
                orchestrator,
                FakeContext(),
                original,
            )

        self.assertEqual(
            result.count(
                "JARVIS GROUNDED ANSWER CONTRACT:"
            ),
            1,
        )

    def test_unknown_plan_preserves_acquisition_guidance(self) -> None:
        orchestrator = FakeOrchestrator()

        with patch(
            "core.conversation.grounded_answer.integration."
            "get_last_qualification_result",
            return_value=QualificationResult(),
        ):
            augment_synthesis_input(
                orchestrator,
                FakeContext(),
                "Prompt",
            )

        plan = get_last_grounded_answer_plan(
            orchestrator
        )

        self.assertEqual(
            plan.state.value,
            "unknown",
        )
        self.assertTrue(
            plan.recommended_action
        )


if __name__ == "__main__":
    unittest.main()
