from __future__ import annotations

import unittest
from core.cognition.decision import (
    DecisionAlternative, DecisionDisposition, DecisionRisk,
    DeterministicDecisionSynthesizer, ExecutiveDecisionService,
    InMemoryDecisionRepository, DecisionRepositoryDisposition,
)
from core.cognition.reasoner import (
    ExecutiveReasoningResult, HypothesisRanking,
    ReasoningDisposition, ReasoningStatus,
)

def reasoning(disposition=ReasoningDisposition.SELECTED, confidence=0.8):
    return ExecutiveReasoningResult(
        reasoning_id="rsn_fixture",
        situation_id="sit_fixture",
        status=ReasoningStatus.COMPLETE,
        disposition=disposition,
        rankings=(
            HypothesisRanking(
                hypothesis_id="hyp_1",
                assessment_id="asm_1",
                rank=1,
                score=0.8,
                confidence=0.9,
                support_score=0.9,
                contradiction_score=0.1,
                coverage=0.9,
            ),
        ),
        selected_hypothesis_id="hyp_1" if disposition is ReasoningDisposition.SELECTED else None,
        confidence=confidence,
        margin=0.5,
        rationale="fixture",
    )

class Tests(unittest.TestCase):
    def setUp(self):
        self.alternatives = (
            DecisionAlternative("alt_a", "Restart service", "Restores health", 0.9, 0.9),
            DecisionAlternative("alt_b", "Observe", "Collect more data", 0.5, 0.8),
        )

    def test_recommends_highest_utility_alternative(self):
        decision = DeterministicDecisionSynthesizer().synthesize(
            reasoning=reasoning(),
            alternatives=self.alternatives,
        )
        self.assertEqual(decision.disposition, DecisionDisposition.RECOMMENDED)
        self.assertEqual(decision.selected_alternative_id, "alt_a")

    def test_defers_without_selected_hypothesis(self):
        decision = DeterministicDecisionSynthesizer().synthesize(
            reasoning=reasoning(ReasoningDisposition.DEFERRED),
            alternatives=self.alternatives,
        )
        self.assertEqual(decision.disposition, DecisionDisposition.DEFERRED)

    def test_escalates_high_risk(self):
        decision = DeterministicDecisionSynthesizer().synthesize(
            reasoning=reasoning(),
            alternatives=self.alternatives,
            risks=(DecisionRisk("risk_1", "Data loss", 0.9, 0.9, "Backup first"),),
        )
        self.assertEqual(decision.disposition, DecisionDisposition.ESCALATION_REQUIRED)

    def test_identity_is_deterministic(self):
        synth = DeterministicDecisionSynthesizer()
        first = synth.synthesize(reasoning=reasoning(), alternatives=self.alternatives)
        second = synth.synthesize(reasoning=reasoning(), alternatives=tuple(reversed(self.alternatives)))
        self.assertEqual(first.decision_id, second.decision_id)

    def test_repository_is_idempotent(self):
        repo = InMemoryDecisionRepository()
        service = ExecutiveDecisionService(repo)
        first = service.synthesize(reasoning=reasoning(), alternatives=self.alternatives)
        second = service.synthesize(reasoning=reasoning(), alternatives=self.alternatives)
        self.assertEqual(first[1], DecisionRepositoryDisposition.CREATED)
        self.assertEqual(second[1], DecisionRepositoryDisposition.DUPLICATE)
        self.assertEqual(repo.count(), 1)

if __name__ == "__main__":
    unittest.main()
