import json
import unittest
from core.retrieval.grounded_answer import AnswerKnowledgeState, GroundedAnswerEngine
from core.retrieval.qualification import (
    EvidenceCandidate, QualificationDecision, QualificationResult,
    QualificationScore, QualifiedEvidence,
)

def accepted(source_id, excerpt, relevance=.9, retrieval=.8):
    return QualifiedEvidence(
        candidate=EvidenceCandidate(
            source_id=source_id, source_path=f"/knowledge/{source_id}.txt",
            title=f"Source {source_id}", subject="grounded answer",
            excerpt=excerpt, backend="runtime_fts",
            retrieval_score=retrieval, metadata={},
        ),
        score=QualificationScore(final=relevance),
        decision=QualificationDecision.ACCEPTED,
        explanation="fixture",
    )

class Tests(unittest.TestCase):
    def setUp(self):
        self.engine = GroundedAnswerEngine()

    def test_unknown(self):
        plan = self.engine.plan("Unknown", QualificationResult())
        self.assertEqual(plan.state, AnswerKnowledgeState.UNKNOWN)

    def test_ranking(self):
        plan = self.engine.plan("Q", QualificationResult(accepted=(
            accepted("low", "Lower evidence.", .5),
            accepted("high", "Higher evidence.", .95),
        )))
        self.assertEqual(plan.ranked_evidence[0].source_id, "high")

    def test_citations(self):
        plan = self.engine.plan("Q", QualificationResult(accepted=(
            accepted("one", "First evidence."),
            accepted("two", "Second evidence."),
        )))
        self.assertEqual([x.citation_id for x in plan.citations], ["C1", "C2"])

    def test_conflict(self):
        plan = self.engine.plan("Is enabled?", QualificationResult(accepted=(
            accepted("a", "The system is enabled and safety control is present."),
            accepted("b", "The system is not enabled and safety control is absent."),
        )))
        self.assertEqual(plan.state, AnswerKnowledgeState.CONFLICTED)
        self.assertTrue(plan.conflicts)

    def test_prompt_contract(self):
        plan = self.engine.plan("Q", QualificationResult(accepted=(accepted("one", "Supported."),)))
        self.assertIn("JARVIS GROUNDED ANSWER CONTRACT:", plan.synthesis_prompt)
        self.assertIn("[C1]", plan.synthesis_prompt)
        self.assertIn("Do not invent missing facts", plan.synthesis_prompt)

    def test_deterministic(self):
        plan = self.engine.plan("Q", QualificationResult(accepted=(accepted("one", "Supported."),)))
        self.assertEqual(self.engine.deterministic_answer(plan), self.engine.deterministic_answer(plan))

    def test_json(self):
        plan = self.engine.plan("Q", QualificationResult(accepted=(accepted("one", "Supported."),)))
        decoded = json.loads(json.dumps(plan.to_dict()))
        self.assertEqual(decoded["citations"][0]["citation_id"], "C1")

if __name__ == "__main__":
    unittest.main()
