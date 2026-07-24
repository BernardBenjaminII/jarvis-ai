import unittest
from core.conversation.grounding import GroundingEvidence, GroundingResult, KnowledgeGap, ObjectiveGrounding
from core.knowledge_awareness import ExecutiveKnowledgeAwarenessService

class ConvergenceC5Tests(unittest.TestCase):
    def test_awareness_reports_answerable_grounded_knowledge(self):
        result=GroundingResult(objectives=(ObjectiveGrounding(
            objective_id="o1", query="zero trust", evidence=tuple(
                GroundingEvidence(f"e{i}","o1","zero trust",f"authoritative statement {i}",f"/source/{i}",.9,"catalog") for i in range(4)
            ), gap=None),), catalog_path="catalog.sqlite")
        state=ExecutiveKnowledgeAwarenessService().assess(result)
        self.assertEqual(state.status, "ready")
        self.assertEqual(state.answerability, "answerable")
        self.assertEqual(state.evidence_count, 4)
        self.assertTrue(state.assessments[0].reasoning_fingerprint)
        self.assertFalse(state.research_queue)

    def test_awareness_declares_gap_and_research_recommendation(self):
        result=GroundingResult(objectives=(ObjectiveGrounding(
            objective_id="o2", query="unknown field", evidence=(),
            gap=KnowledgeGap("o2","unknown field","No catalog evidence.")),), catalog_path="catalog.sqlite")
        state=ExecutiveKnowledgeAwarenessService().assess(result)
        self.assertEqual(state.status, "unknown")
        self.assertEqual(state.answerability, "insufficient")
        self.assertEqual(len(state.research_queue), 1)
        self.assertEqual(state.research_queue[0].priority, "high")

    def test_state_is_deterministic(self):
        result=GroundingResult(objectives=(ObjectiveGrounding(
            objective_id="o1", query="topic", evidence=(GroundingEvidence("e1","o1","topic","statement","/a",.8,"catalog"),), gap=None),), catalog_path="x")
        svc=ExecutiveKnowledgeAwarenessService()
        self.assertEqual(svc.assess(result).to_dict(), svc.assess(result).to_dict())

if __name__ == "__main__": unittest.main()
