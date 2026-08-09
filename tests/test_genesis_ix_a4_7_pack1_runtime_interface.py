from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
import unittest

from core.conversation.grounded_answer import (
    GroundedAnswerExecutionRequest,
    GroundedAnswerRuntimeContext,
    GroundedAnswerRuntimeService,
)
from core.retrieval.qualification import (
    EvidenceCandidate,
    QualificationDecision,
    QualificationResult,
    QualificationScore,
    QualifiedEvidence,
)


def qualification() -> QualificationResult:
    candidate = EvidenceCandidate(
        source_id="source-1",
        source_path="/knowledge/source-1.txt",
        title="Grounded Runtime Interface",
        subject="executive conversation",
        excerpt=(
            "The runtime interface adapts qualified evidence into a grounded "
            "answer plan."
        ),
        backend="certification",
        retrieval_score=0.9,
        metadata={},
    )
    evidence = QualifiedEvidence(
        candidate=candidate,
        score=QualificationScore(final=0.9),
        decision=QualificationDecision.ACCEPTED,
        explanation="Relevant.",
    )
    return QualificationResult(accepted=(evidence,))


def request() -> GroundedAnswerExecutionRequest:
    return GroundedAnswerExecutionRequest(
        context=GroundedAnswerRuntimeContext(
            request_id="req-1",
            session_id="session-1",
            operator_input="What does the runtime interface do?",
            metadata={"workspace": "knowledge"},
        ),
        qualification=qualification(),
    )


class GenesisIXA47Pack1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GroundedAnswerRuntimeService.create_default()

    def test_context_is_immutable(self) -> None:
        context = request().context

        with self.assertRaises(FrozenInstanceError):
            context.mode = "changed"

    def test_plan_does_not_invoke_synthesis(self) -> None:
        response = self.service.plan(request())

        self.assertFalse(response.synthesis_invoked)
        self.assertIsNone(response.answer)
        self.assertTrue(response.citations)

    def test_execute_invokes_synthesis(self) -> None:
        calls = []

        def synthesize(prompt: str) -> str:
            calls.append(prompt)
            return "Grounded response [C1]."

        response = self.service.execute(
            request(),
            synthesize,
        )

        self.assertTrue(response.synthesis_invoked)
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            response.answer.answer,
            "Grounded response [C1].",
        )

    def test_response_exposes_plan_metadata(self) -> None:
        response = self.service.plan(request())

        self.assertEqual(response.state, response.plan.state.value)
        self.assertEqual(response.confidence, response.plan.confidence)
        self.assertEqual(response.metadata["behavior_change"], False)

    def test_json_serialization(self) -> None:
        response = self.service.plan(request())
        payload = json.loads(
            json.dumps(response.to_dict(), sort_keys=True)
        )

        self.assertEqual(payload["state"], response.state)
        self.assertFalse(payload["synthesis_invoked"])

    def test_default_service_owns_engine(self) -> None:
        self.assertIsNotNone(self.service.engine)

    def test_public_import_surface(self) -> None:
        import core.conversation.grounded_answer as package

        expected = {
            "GroundedAnswerExecutionRequest",
            "GroundedAnswerExecutionResponse",
            "GroundedAnswerRuntimeContext",
            "GroundedAnswerRuntimeService",
        }

        self.assertTrue(
            expected.issubset(set(package.__all__))
        )


if __name__ == "__main__":
    unittest.main()
