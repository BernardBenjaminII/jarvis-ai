from dataclasses import dataclass
import unittest
from core.cognition.coa import *

@dataclass(frozen=True)
class ReasoningFixture:
    reasoning_id: str = "reasoning-001"
    selected_hypothesis_id: str = "hypothesis-001"
    confidence: float = 0.8

def templates():
    return (
        CourseOfActionTemplate(template_id="balanced", kind=CourseOfActionKind.BALANCED, title_pattern="Balanced response to {hypothesis_id}", description_pattern="Act proportionately on {hypothesis_id}.", base_utility=.8, base_confidence=.8, objectives=("Resolve condition",), expected_outcomes=("Condition stabilized",)),
        CourseOfActionTemplate(template_id="aggressive", kind=CourseOfActionKind.AGGRESSIVE, title_pattern="Rapid response to {hypothesis_id}", description_pattern="Act rapidly on {hypothesis_id}.", base_utility=.9, base_confidence=.5, objectives=("Resolve quickly",), expected_outcomes=("Condition contained",)),
    )

class Tests(unittest.TestCase):
    def setUp(self): self.generator = DeterministicCourseOfActionGenerator()
    def test_generates_ranked_courses_of_action(self):
        result=self.generator.generate(ReasoningFixture(), templates())
        self.assertEqual(result.disposition, GenerationDisposition.GENERATED)
        self.assertGreaterEqual(len(result.courses_of_action), 4)
        self.assertGreaterEqual(result.courses_of_action[0].rank_score, result.courses_of_action[-1].rank_score)
    def test_mandatory_hold_and_contingency_are_present(self):
        result=self.generator.generate(ReasoningFixture(), templates())
        kinds={c.kind for c in result.courses_of_action}
        self.assertIn(CourseOfActionKind.HOLD, kinds); self.assertIn(CourseOfActionKind.CONTINGENCY, kinds)
    def test_defers_without_selected_hypothesis(self):
        result=self.generator.generate(ReasoningFixture(selected_hypothesis_id=""), templates())
        self.assertEqual(result.disposition, GenerationDisposition.DEFERRED)
    def test_identity_is_deterministic(self):
        a=self.generator.generate(ReasoningFixture(), templates()); b=self.generator.generate(ReasoningFixture(), templates())
        self.assertEqual(a.generation_id,b.generation_id); self.assertEqual([c.coa_id for c in a.courses_of_action],[c.coa_id for c in b.courses_of_action])
    def test_repository_is_idempotent(self):
        repo=InMemoryCourseOfActionRepository(); service=ExecutiveAlternativeGenerationService(self.generator,repo)
        self.assertEqual(service.generate(ReasoningFixture(),templates()).disposition,GenerationDisposition.GENERATED)
        self.assertEqual(service.generate(ReasoningFixture(),templates()).disposition,GenerationDisposition.DUPLICATE)
    def test_decision_adapter_is_neutral(self):
        result=self.generator.generate(ReasoningFixture(),templates()); data=result.courses_of_action[0].as_decision_alternative_kwargs()
        self.assertEqual(data["alternative_id"],result.courses_of_action[0].coa_id); self.assertIn("expected_utility",data)

if __name__ == "__main__": unittest.main()
