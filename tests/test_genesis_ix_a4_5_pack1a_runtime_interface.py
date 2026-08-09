from __future__ import annotations
import json
from dataclasses import FrozenInstanceError
import unittest
from core.retrieval.qualification import *

def fixture():
    return EvidenceCandidate(
        source_id="doc-1",
        source_path="/knowledge/doc-1.txt",
        title="Test",
        subject="retrieval",
        excerpt="qualification contract",
        backend="runtime_fts",
        retrieval_score=0.75,
        metadata={"rank": 1},
    )

class Tests(unittest.TestCase):
    def test_candidate_immutable(self):
        item = fixture()
        with self.assertRaises(FrozenInstanceError):
            item.title = "x"

    def test_score_clamped(self):
        score = QualificationScore(lexical=-1, semantic=2, final=1.5)
        self.assertEqual((score.lexical, score.semantic, score.final), (0.0, 1.0, 1.0))

    def test_enum_stable(self):
        self.assertEqual(QualificationDecision.ACCEPTED.value, "accepted")

    def test_acceptance_derived(self):
        item = QualifiedEvidence(fixture(), QualificationScore(final=.9), QualificationDecision.ACCEPTED)
        self.assertTrue(item.accepted)

    def test_partitions(self):
        accepted = QualifiedEvidence(fixture(), QualificationScore(final=.9), QualificationDecision.ACCEPTED)
        rejected = QualifiedEvidence(fixture(), QualificationScore(final=.1), QualificationDecision.REJECTED_LOW_RELEVANCE)
        result = QualificationResult((accepted,), (rejected,), .25, {"backend":"runtime_fts"})
        self.assertEqual(result.total_candidates, 2)
        self.assertTrue(result.has_accepted_evidence)

    def test_invalid_partition(self):
        rejected = QualifiedEvidence(fixture(), QualificationScore(final=.1), QualificationDecision.REJECTED_LOW_RELEVANCE)
        with self.assertRaises(ValueError):
            QualificationResult(accepted=(rejected,))

    def test_json(self):
        accepted = QualifiedEvidence(fixture(), QualificationScore(final=.9), QualificationDecision.ACCEPTED)
        decoded = json.loads(json.dumps(QualificationResult((accepted,), threshold=.25).to_dict()))
        self.assertEqual(decoded["accepted"][0]["decision"], "accepted")

    def test_metadata_copy(self):
        metadata = {"rank":1}
        item = EvidenceCandidate("x","/x","x","x","x","fts",.5,metadata)
        metadata["rank"] = 9
        self.assertEqual(item.metadata["rank"], 1)

    def test_import_surface(self):
        import core.retrieval.qualification as q
        self.assertIn("QualificationResult", q.__all__)

if __name__ == "__main__":
    unittest.main()
