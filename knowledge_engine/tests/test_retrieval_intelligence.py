"""Tests for Phase V-B.5 Retrieval Intelligence."""

from __future__ import annotations

import unittest

from knowledge_engine.retrieval_intelligence import (
    CandidateFilter,
    CandidateMerger,
    RetrievalDirector,
    StaticRetrievalProvider,
    confidence_label,
)
from knowledge_engine.retrieval_intelligence.normalization import (
    normalize_candidate,
    normalize_similarity,
)


class SimilarityNormalizationTests(unittest.TestCase):
    def test_negative_cosine_is_translated(self) -> None:
        self.assertAlmostEqual(
            normalize_similarity(-0.06),
            0.47,
        )

    def test_positive_similarity_is_preserved(self) -> None:
        self.assertAlmostEqual(
            normalize_similarity(0.82),
            0.82,
        )

    def test_percentage_is_normalized(self) -> None:
        self.assertAlmostEqual(
            normalize_similarity(85),
            0.85,
        )


class CandidateNormalizationTests(unittest.TestCase):
    def test_vector_tuple_is_normalized(self) -> None:
        candidate = normalize_candidate(
            (
                0.79,
                "/docs/sqlite.pdf",
                4,
                "SQLite indexes reduce table scans.",
            ),
            provider="vector",
        )

        self.assertEqual(candidate.source, "/docs/sqlite.pdf")
        self.assertEqual(candidate.chunk_index, 4)
        self.assertAlmostEqual(candidate.raw_score, 0.79)
        self.assertAlmostEqual(candidate.normalized_score, 0.79)
        self.assertEqual(candidate.provider, "vector")


class CandidateFilterTests(unittest.TestCase):
    def test_irrelevant_negative_similarity_is_rejected(self) -> None:
        filter_service = CandidateFilter(
            minimum_similarity=0.55
        )

        candidate = normalize_candidate(
            (
                -0.06,
                "/docs/unrelated.pdf",
                0,
                "Unrelated content.",
            ),
            provider="vector",
        )

        accepted, rejected = filter_service.apply([candidate])

        self.assertEqual(accepted, [])
        self.assertEqual(rejected, [candidate])

    def test_strong_similarity_is_accepted(self) -> None:
        filter_service = CandidateFilter(
            minimum_similarity=0.55
        )

        candidate = normalize_candidate(
            (
                0.81,
                "/docs/sqlite.pdf",
                0,
                "SQLite embeddings and vector retrieval.",
            ),
            provider="vector",
        )

        accepted, rejected = filter_service.apply([candidate])

        self.assertEqual(accepted, [candidate])
        self.assertEqual(rejected, [])


class CandidateMergerTests(unittest.TestCase):
    def test_duplicate_identity_keeps_strongest_candidate(self) -> None:
        vector = normalize_candidate(
            (
                0.72,
                "/docs/sqlite.pdf",
                2,
                "SQLite query planning.",
            ),
            provider="vector",
        )

        metadata = normalize_candidate(
            (
                0.91,
                "/docs/sqlite.pdf",
                2,
                "SQLite query planning.",
            ),
            provider="metadata",
        )

        merged = CandidateMerger().merge(
            [
                [vector],
                [metadata],
            ]
        )

        self.assertEqual(len(merged), 1)
        self.assertAlmostEqual(
            merged[0].normalized_score,
            0.91,
        )


class RetrievalDirectorTests(unittest.TestCase):
    def test_director_filters_weak_candidates(self) -> None:
        provider = StaticRetrievalProvider(
            name="vector",
            candidates=[
                (
                    -0.06,
                    "/docs/unrelated.pdf",
                    0,
                    "Unrelated content.",
                ),
                (
                    0.83,
                    "/docs/sqlite.pdf",
                    1,
                    "SQLite embeddings support semantic retrieval.",
                ),
            ],
        )

        director = RetrievalDirector(
            providers=[provider],
            minimum_similarity=0.55,
        )

        results = director.search(
            "SQLite embeddings",
            limit=5,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["source"],
            "/docs/sqlite.pdf",
        )

        diagnostics = director.last_diagnostics

        self.assertIsNotNone(diagnostics)
        self.assertEqual(
            diagnostics.retrieved_candidates,
            2,
        )
        self.assertEqual(
            diagnostics.accepted_candidates,
            1,
        )
        self.assertEqual(
            diagnostics.rejected_candidates,
            1,
        )

    def test_director_merges_multiple_providers(self) -> None:
        vector = StaticRetrievalProvider(
            name="vector",
            candidates=[
                (
                    0.74,
                    "/docs/sqlite.pdf",
                    1,
                    "SQLite query planner.",
                )
            ],
        )

        metadata = StaticRetrievalProvider(
            name="metadata",
            candidates=[
                (
                    0.91,
                    "/docs/sqlite.pdf",
                    1,
                    "SQLite query planner.",
                ),
                (
                    0.79,
                    "/docs/database-indexes.pdf",
                    3,
                    "Database indexing and retrieval.",
                ),
            ],
        )

        director = RetrievalDirector(
            providers=[vector, metadata],
            minimum_similarity=0.55,
        )

        results = director.search(
            "SQLite indexes",
            limit=5,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0]["source"],
            "/docs/sqlite.pdf",
        )
        self.assertEqual(
            director.last_diagnostics.provider_count,
            2,
        )

    def test_no_results_produces_none_confidence(self) -> None:
        provider = StaticRetrievalProvider(
            name="vector",
            candidates=[
                (
                    -0.50,
                    "/docs/unrelated.pdf",
                    0,
                    "Unrelated.",
                )
            ],
        )

        director = RetrievalDirector(
            providers=[provider],
            minimum_similarity=0.55,
        )

        results = director.search(
            "SQLite",
            limit=5,
        )

        self.assertEqual(results, [])
        self.assertEqual(
            director.last_diagnostics.confidence,
            "none",
        )

    def test_confidence_labels(self) -> None:
        high = [
            normalize_candidate(
                (
                    0.90,
                    "/docs/a.pdf",
                    0,
                    "Strong result.",
                ),
                provider="vector",
            ),
            normalize_candidate(
                (
                    0.80,
                    "/docs/b.pdf",
                    0,
                    "Strong result.",
                ),
                provider="vector",
            ),
        ]

        self.assertEqual(
            confidence_label(high),
            "high",
        )


if __name__ == "__main__":
    unittest.main()
