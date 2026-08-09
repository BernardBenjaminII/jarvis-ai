from __future__ import annotations

import unittest

from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
    clear_last_qualification_state,
    get_last_qualification_result,
    get_last_qualification_trace,
    qualify_rows,
)


class GenesisIXA47Pack2ATests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_last_qualification_state()

    def test_result_is_retained(self) -> None:
        rows, result = qualify_rows(
            "UH-60 hydraulic maintenance",
            [
                {
                    "file_path": "/knowledge/uh60.txt",
                    "title": "UH-60 Hydraulic Maintenance Manual",
                    "subject": "UH-60 hydraulic maintenance",
                    "excerpt": (
                        "Black Hawk hydraulic maintenance procedures."
                    ),
                    "confidence": 0.9,
                }
            ],
        )

        self.assertIs(
            get_last_qualification_result(),
            result,
        )
        self.assertEqual(len(rows), 1)

    def test_trace_is_retained(self) -> None:
        qualify_rows(
            "Quantum Banana Warp Core Mk XII",
            [
                {
                    "file_path": "/knowledge/electronics.txt",
                    "title": "Practical Electronics Handbook",
                    "subject": "computer architecture",
                    "excerpt": "Von Neumann architecture.",
                    "confidence": 0.08,
                }
            ],
        )

        trace = get_last_qualification_trace()

        self.assertIsNotNone(trace)
        self.assertEqual(trace["accepted_count"], 0)
        self.assertEqual(trace["rejected_count"], 1)

    def test_clear_state(self) -> None:
        qualify_rows(
            "anything",
            [],
        )

        clear_last_qualification_state()

        self.assertIsNone(
            get_last_qualification_result()
        )
        self.assertIsNone(
            get_last_qualification_trace()
        )

    def test_candidate_normalization_is_preserved(self) -> None:
        candidate = candidate_from_row(
            {
                "file_path": "/knowledge/manual.txt",
                "subject": "maintenance",
                "excerpt": "Maintenance procedures.",
                "confidence": 0.8,
            },
            ordinal=1,
        )

        self.assertEqual(
            candidate.source_path,
            "/knowledge/manual.txt",
        )
        self.assertEqual(
            candidate.subject,
            "maintenance",
        )

    def test_result_and_trace_are_request_local_objects(self) -> None:
        qualify_rows(
            "first query",
            [],
        )
        first_result = get_last_qualification_result()
        first_trace = get_last_qualification_trace()

        qualify_rows(
            "second query",
            [],
        )
        second_result = get_last_qualification_result()
        second_trace = get_last_qualification_trace()

        self.assertIsNot(
            first_result,
            second_result,
        )
        self.assertEqual(
            first_trace["query"],
            "first query",
        )
        self.assertEqual(
            second_trace["query"],
            "second query",
        )


if __name__ == "__main__":
    unittest.main()
