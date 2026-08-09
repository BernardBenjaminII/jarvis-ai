from __future__ import annotations
import unittest
from core.retrieval.qualification import *

def c(title, subject, excerpt, score=.8):
    return EvidenceCandidate(title,f"/knowledge/{title}.txt",title,subject,excerpt,"runtime_fts",score,{})

class Tests(unittest.TestCase):
    def setUp(self):
        self.engine = QualificationEngine()

    def test_relevant_accept(self):
        result = self.engine.evaluate(
            "UH-60 Black Hawk hydraulic system maintenance",
            [c("UH-60 Hydraulic Maintenance Manual","UH-60 hydraulic systems",
               "Black Hawk hydraulic system maintenance procedures.")],
        )
        self.assertEqual(len(result.accepted),1)

    def test_fabricated_reject(self):
        result = self.engine.evaluate(
            "Quantum Banana Warp Core Mk XII",
            [c("Practical Electronics Handbook","computer architecture",
               "Von Neumann architecture and digital electronics.",.08)],
        )
        self.assertEqual(len(result.accepted),0)
        self.assertEqual(len(result.rejected),1)

    def test_exact_phrase_higher(self):
        exact = self.engine.evaluate_candidate(
            "Quantum Banana Warp Core Mk XII",
            c("Quantum Banana Warp Core Mk XII","fictional propulsion",
              "Quantum Banana Warp Core Mk XII technical manual."),
        )
        scattered = self.engine.evaluate_candidate(
            "Quantum Banana Warp Core Mk XII",
            c("Quantum Computing","banana agriculture",
              "Warp knitting and processor core design."),
        )
        self.assertGreater(exact.score.final, scattered.score.final)

    def test_low_confidence(self):
        item = self.engine.evaluate_candidate(
            "retrieval qualification engine",
            c("Retrieval Qualification Engine","retrieval qualification","Relevant text.",.001),
        )
        self.assertEqual(item.decision, QualificationDecision.REJECTED_LOW_CONFIDENCE)

    def test_empty(self):
        result = self.engine.evaluate("anything", [])
        self.assertTrue(result.runtime_statistics["empty_result"])

    def test_deterministic(self):
        item = c("Evidence Qualification","retrieval","Evidence qualification relevance.")
        self.assertEqual(
            self.engine.evaluate_candidate("evidence qualification",item).to_dict(),
            self.engine.evaluate_candidate("evidence qualification",item).to_dict(),
        )

if __name__ == "__main__":
    unittest.main()
