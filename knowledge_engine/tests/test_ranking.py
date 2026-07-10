"""Tests for the JARVIS Knowledge Ranking Engine."""

from __future__ import annotations

import unittest

from knowledge_engine.ranking import KnowledgeRanker, RankingWeights
from knowledge_engine.ranking.duplicates import duplicate_similarity
from knowledge_engine.ranking.normalization import (
    normalize_candidate,
    normalize_semantic_score,
)
from knowledge_engine.ranking.scorer import (
    authority_score,
    completeness_score,
    lexical_score,
)


class RankingNormalizationTests(unittest.TestCase):
    def test_percentage_score_is_normalized(self) -> None:
        self.assertAlmostEqual(normalize_semantic_score(85), 0.85)

    def test_similarity_score_is_preserved(self) -> None:
        self.assertAlmostEqual(normalize_semantic_score(0.72), 0.72)

    def test_mapping_candidate_is_normalized(self) -> None:
        candidate = normalize_candidate(
            {
                "content": "SQLite stores data in a portable database file.",
                "file_path": "/docs/sqlite-reference.pdf",
                "chunk_number": 4,
                "score": 0.80,
                "quality": 92,
            }
        )

        self.assertEqual(
            candidate.text,
            "SQLite stores data in a portable database file.",
        )
        self.assertEqual(candidate.chunk_index, 4)
        self.assertAlmostEqual(candidate.semantic_score, 0.80)
        self.assertAlmostEqual(candidate.quality_score, 0.92)


class RankingScorerTests(unittest.TestCase):
    def test_lexical_match_beats_unrelated_text(self) -> None:
        query = "SQLite database transactions"

        related = lexical_score(
            query,
            "SQLite supports atomic database transactions.",
        )
        unrelated = lexical_score(
            query,
            "A helicopter rotor system creates lift.",
        )

        self.assertGreater(related, unrelated)

    def test_complete_text_beats_fragment(self) -> None:
        complete = completeness_score(
            "SQLite transactions are atomic, consistent, isolated, and "
            "durable. The database engine uses a journal or write-ahead "
            "log to preserve recoverability."
        )
        fragment = completeness_score("SQLite transactions")

        self.assertGreater(complete, fragment)

    def test_reference_path_receives_authority_credit(self) -> None:
        reference = authority_score("/docs/reference/sqlite-manual.pdf")
        temporary = authority_score("/tmp/backup/sqlite-copy.txt")

        self.assertGreater(reference, temporary)


class DuplicateTests(unittest.TestCase):
    def test_identical_results_are_duplicates(self) -> None:
        left = normalize_candidate(
            {
                "text": "SQLite supports atomic transactions.",
                "source": "/docs/sqlite.pdf",
                "chunk_index": 1,
            }
        )
        right = normalize_candidate(
            {
                "text": "SQLite supports atomic transactions.",
                "source": "/docs/sqlite.pdf",
                "chunk_index": 2,
            }
        )

        self.assertEqual(duplicate_similarity(left, right), 1.0)


class KnowledgeRankerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ranker = KnowledgeRanker()

    def test_weights_total_one(self) -> None:
        weights = RankingWeights()

        total = (
            weights.semantic
            + weights.lexical
            + weights.quality
            + weights.authority
            + weights.completeness
            + weights.freshness
            + weights.diversity
        )

        self.assertAlmostEqual(total, 1.0)

    def test_relevant_result_ranks_first(self) -> None:
        results = [
            {
                "text": (
                    "SQLite transactions are atomic and can use "
                    "write-ahead logging."
                ),
                "source": "/docs/reference/sqlite-manual.pdf",
                "chunk_index": 8,
                "score": 0.88,
                "quality": 96,
            },
            {
                "text": "Ahmed Deedat was born in India in 1918.",
                "source": "/ebooks/biography.pdf",
                "chunk_index": 0,
                "score": 0.04,
                "quality": 100,
            },
            {
                "text": "Use UltraISO to extract MP3 files.",
                "source": "/downloads/read-me.txt",
                "chunk_index": 0,
                "score": 0.03,
                "quality": 100,
            },
        ]

        ranked = self.ranker.rank(
            "SQLite database transactions",
            results,
            limit=3,
        )

        self.assertEqual(
            ranked[0]["source"],
            "/docs/reference/sqlite-manual.pdf",
        )
        self.assertGreater(
            ranked[0]["ranking_score"],
            ranked[1]["ranking_score"],
        )

    def test_duplicate_penalty_promotes_source_diversity(self) -> None:
        results = [
            {
                "text": (
                    "SQLite supports atomic database transactions and "
                    "write-ahead logging."
                ),
                "source": "/docs/sqlite-a.pdf",
                "chunk_index": 1,
                "score": 0.90,
                "quality": 95,
            },
            {
                "text": (
                    "SQLite supports atomic database transactions and "
                    "write-ahead logging."
                ),
                "source": "/docs/sqlite-a.pdf",
                "chunk_index": 2,
                "score": 0.89,
                "quality": 95,
            },
            {
                "text": (
                    "SQLite provides transaction isolation and durable "
                    "commit behavior."
                ),
                "source": "/docs/sqlite-b.pdf",
                "chunk_index": 4,
                "score": 0.84,
                "quality": 93,
            },
        ]

        ranked = self.ranker.rank(
            "SQLite database transactions",
            results,
            limit=2,
        )

        self.assertEqual(ranked[0]["source"], "/docs/sqlite-a.pdf")
        self.assertEqual(ranked[1]["source"], "/docs/sqlite-b.pdf")

    def test_ranking_is_explainable(self) -> None:
        ranked = self.ranker.rank(
            "Python generators",
            [
                {
                    "text": (
                        "Python generators yield values lazily and preserve "
                        "execution state between iterations."
                    ),
                    "source": "/docs/python-reference.pdf",
                    "chunk_index": 12,
                    "score": 0.86,
                    "quality": 90,
                }
            ],
        )

        explanation = ranked[0]["ranking"]

        self.assertIn("semantic", explanation)
        self.assertIn("lexical", explanation)
        self.assertIn("authority", explanation)
        self.assertIn("duplicate_penalty", explanation)
        self.assertIn("final_score", explanation)


if __name__ == "__main__":
    unittest.main()
