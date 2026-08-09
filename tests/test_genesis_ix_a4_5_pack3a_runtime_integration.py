from __future__ import annotations
import unittest
from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
    get_last_qualification_trace,
    qualify_rows,
)

class Tests(unittest.TestCase):
    def test_row_normalization(self):
        candidate = candidate_from_row({
            "file_path": "/knowledge/manual.txt",
            "subject": "UH-60 hydraulic systems",
            "excerpt": "Black Hawk hydraulic maintenance.",
            "confidence": 0.8,
        }, ordinal=1)
        self.assertEqual(candidate.source_path, "/knowledge/manual.txt")

    def test_relevant_row_survives(self):
        rows, result = qualify_rows(
            "UH-60 Black Hawk hydraulic system maintenance",
            [{
                "file_path": "/knowledge/uh60.txt",
                "title": "UH-60 Hydraulic Maintenance Manual",
                "subject": "UH-60 hydraulic systems",
                "excerpt": "Black Hawk hydraulic system maintenance procedures.",
                "confidence": 0.85,
            }],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(result.accepted), 1)
        self.assertIn("qualification_score", rows[0])

    def test_false_positive_filtered(self):
        rows, result = qualify_rows(
            "Quantum Banana Warp Core Mk XII",
            [{
                "file_path": "/knowledge/electronics.txt",
                "title": "Practical Electronics Handbook",
                "subject": "computer architecture",
                "excerpt": "Von Neumann architecture and digital electronics.",
                "confidence": 0.08,
            }],
        )
        self.assertEqual(rows, [])
        self.assertEqual(len(result.rejected), 1)

    def test_trace_available(self):
        qualify_rows(
            "Quantum Banana Warp Core Mk XII",
            [{
                "file_path": "/knowledge/electronics.txt",
                "subject": "computer architecture",
                "excerpt": "Von Neumann architecture.",
                "confidence": 0.08,
            }],
        )
        trace = get_last_qualification_trace()
        self.assertEqual(trace["accepted_count"], 0)
        self.assertEqual(trace["rejected_count"], 1)

if __name__ == "__main__":
    unittest.main()
