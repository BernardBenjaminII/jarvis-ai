import unittest

from core.retrieval.evidence_context.precision import passes_precision_gate
from core.retrieval.evidence_context.dedup import (
    evidence_fingerprint,
    overlap_ratio,
)


class GenesisXB23Tests(unittest.TestCase):
    def test_precision_gate_rejects_zero_concept_signal(self):
        self.assertFalse(
            passes_precision_gate(
                hybrid_score=0.70,
                semantic_score=0.75,
                lexical_score=0.0,
                title_score=0.0,
            )
        )

    def test_precision_gate_accepts_hybrid_evidence(self):
        self.assertTrue(
            passes_precision_gate(
                hybrid_score=0.70,
                semantic_score=0.72,
                lexical_score=1.0,
                title_score=0.5,
            )
        )

    def test_fingerprint_normalizes_case_and_spacing(self):
        self.assertEqual(
            evidence_fingerprint("C++  iterators\nwork"),
            evidence_fingerprint("c++ iterators work"),
        )

    def test_overlap_ratio_detects_near_duplicate(self):
        a = "C++ iterators traverse containers and work with STL algorithms"
        b = "STL algorithms work with C++ iterators that traverse containers"
        self.assertGreaterEqual(overlap_ratio(a, b), 0.75)


if __name__ == "__main__":
    unittest.main()
