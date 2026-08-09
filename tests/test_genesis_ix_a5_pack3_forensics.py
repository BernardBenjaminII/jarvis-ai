from __future__ import annotations

import unittest

from dev.qualification_forensics.extract import (
    candidate_record,
    infer_rejection_reason,
)


class GenesisIXA5Pack3Tests(unittest.TestCase):
    def test_lexical_reason_from_explanation(self) -> None:
        reason = infer_rejection_reason(
            decision="REJECTED_LOW_RELEVANCE",
            explanation="lexical 0.000 below 0.200",
            lexical=0.0,
            phrase=0.2,
            subject=0.3,
            confidence=0.4,
            final=0.1,
            threshold=0.2,
        )
        self.assertEqual(reason, "LEXICAL")

    def test_final_threshold_reason(self) -> None:
        reason = infer_rejection_reason(
            decision="REJECTED",
            explanation="",
            lexical=None,
            phrase=None,
            subject=None,
            confidence=None,
            final=0.45,
            threshold=0.6,
        )
        self.assertEqual(reason, "FINAL_THRESHOLD")

    def test_candidate_record_margin(self) -> None:
        record = candidate_record(
            {
                "source_id": "c1",
                "title": "SQLite",
                "qualification_decision": "REJECTED",
                "qualification_score": 0.45,
                "qualification_explanation": "below threshold",
                "qualification_components": {
                    "lexical": 0.5,
                    "phrase": 0.4,
                    "subject": 0.7,
                    "confidence": 0.6,
                    "final": 0.45,
                },
            },
            raw_rank=1,
            threshold=0.6,
        )
        self.assertAlmostEqual(record.score_margin, -0.15)
        self.assertEqual(record.rejection_reason, "FINAL_THRESHOLD")

    def test_accepted_has_no_rejection_reason(self) -> None:
        record = candidate_record(
            {
                "source_id": "c2",
                "title": "SHA-256",
                "qualification_decision": "ACCEPTED",
                "qualification_score": 0.9,
                "qualification_components": {
                    "lexical": 1.0,
                    "phrase": 0.8,
                    "subject": 0.8,
                    "confidence": 0.9,
                    "final": 0.9,
                },
            },
            raw_rank=1,
            threshold=0.6,
        )
        self.assertIsNone(record.rejection_reason)


if __name__ == "__main__":
    unittest.main()
