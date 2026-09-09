from __future__ import annotations

import unittest

from core.knowledge_catalog.materialization.search import _fts_query
from core.retrieval.qualification import (
    EvidenceCandidate,
    QualificationEngine,
)


class GenesisXB2RetrievalIntegrityTests(unittest.TestCase):

    def test_question_framing_does_not_become_fts_query(self):
        self.assertEqual(
            _fts_query("What is C++?"),
            "",
        )

    def test_substantive_terms_survive_question_framing(self):
        self.assertEqual(
            _fts_query("What is C++ programming?"),
            '"programming"',
        )

    def test_normal_word_query_survives(self):
        self.assertEqual(
            _fts_query("What is NATO?"),
            '"nato"',
        )

    def test_unrelated_text_cannot_win_by_phrase_override(self):
        candidate = EvidenceCandidate(
            "on-liberty",
            "/knowledge/philosophy/on-liberty.pdf",
            "On Liberty",
            "philosophy",
            (
                "The difficulty then was to induce men of strong bodies or "
                "minds to pay obedience to rules and control their impulses."
            ),
            "runtime_materialization_fts",
            0.75,
            {},
        )

        result = QualificationEngine().evaluate(
            "What is C++?",
            (candidate,),
        )

        self.assertEqual(len(result.accepted), 0)
        self.assertEqual(len(result.rejected), 1)
        self.assertEqual(
            result.rejected[0].score.lexical,
            0.0,
        )

    def test_relevant_cpp_evidence_can_qualify(self):
        candidate = EvidenceCandidate(
            "cpp-reference",
            "/knowledge/programming/cpp-reference.txt",
            "C++ Programming",
            "C++ programming",
            (
                "C++ is a general-purpose programming language. "
                "It supports procedural, object-oriented, generic, "
                "and systems programming."
            ),
            "runtime_materialization_fts",
            0.75,
            {},
        )

        result = QualificationEngine().evaluate(
            "What is C++?",
            (candidate,),
        )

        self.assertEqual(len(result.accepted), 1)
        self.assertGreater(
            result.accepted[0].score.lexical,
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
