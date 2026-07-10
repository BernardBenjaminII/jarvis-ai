"""Tests for Phase V-B production ranked-search integration."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from knowledge_engine.search.service import SearchService


class FakeQualityReport:
    """Minimal quality-report fixture used by search-service tests."""

    def __init__(self, score: int) -> None:
        self.score = score


class RankedSearchServiceTests(unittest.TestCase):
    """Regression coverage for ranked production search."""

    def setUp(self) -> None:
        self.database = Mock()

    @patch("knowledge_engine.search.service.QualityService")
    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_search_retrieves_broad_candidate_pool(
        self,
        director_class,
        ranking_class,
        quality_service,
    ) -> None:
        quality_service.validator.validate_chunk.return_value = (
            FakeQualityReport(95)
        )

        director = director_class.return_value
        director.search.return_value = [
            {
                "score": 0.82,
                "source": "/docs/sqlite.pdf",
                "chunk_index": 3,
                "text": "SQLite indexes improve query performance.",
            }
        ]

        ranking = ranking_class.return_value
        ranking.rank.side_effect = (
            lambda query, results, limit=None: results[:limit]
        )

        service = SearchService(self.database)

        service.execute(
            "SQLite indexes",
            limit=5,
        )

        director.search.assert_called_once_with(
            query="SQLite indexes",
            limit=20,
        )

        ranking.rank.assert_called_once()

        self.assertEqual(
            ranking.rank.call_args.args[0],
            "SQLite indexes",
        )

        self.assertEqual(
            ranking.rank.call_args.kwargs["limit"],
            5,
        )

    @patch("knowledge_engine.search.service.QualityService")
    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_retrieval_mapping_is_normalized_for_ranking(
        self,
        director_class,
        ranking_class,
        quality_service,
    ) -> None:
        quality_service.validator.validate_chunk.return_value = (
            FakeQualityReport(93)
        )

        director_class.return_value.search.return_value = [
            {
                "score": 0.78,
                "source": "/docs/database.pdf",
                "chunk_index": 7,
                "text": "Database indexes reduce full table scans.",
            }
        ]

        ranking_class.return_value.rank.side_effect = (
            lambda query, results, limit=None: results
        )

        service = SearchService(self.database)

        service.execute(
            "database indexes",
            limit=1,
        )

        candidates = (
            ranking_class
            .return_value
            .rank
            .call_args
            .args[1]
        )

        candidate = candidates[0]

        self.assertEqual(
            candidate["source"],
            "/docs/database.pdf",
        )

        self.assertEqual(
            candidate["chunk_index"],
            7,
        )

        self.assertAlmostEqual(
            candidate["semantic_score"],
            0.78,
        )

        self.assertEqual(
            candidate["quality"],
            93,
        )

    @patch("knowledge_engine.search.service.QualityService")
    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_ranked_order_becomes_final_result_order(
        self,
        director_class,
        ranking_class,
        quality_service,
    ) -> None:
        quality_service.validator.validate_chunk.side_effect = [
            FakeQualityReport(90),
            FakeQualityReport(97),
        ]

        director_class.return_value.search.return_value = [
            {
                "score": 0.91,
                "source": "/notes/hydraulics.txt",
                "chunk_index": 1,
                "text": "Aircraft hydraulic servicing procedures.",
            },
            {
                "score": 0.84,
                "source": "/docs/reference/sqlite-manual.pdf",
                "chunk_index": 8,
                "text": "SQLite indexes reduce full table scans.",
            },
        ]

        ranking_class.return_value.rank.return_value = [
            {
                "text": "SQLite indexes reduce full table scans.",
                "source": "/docs/reference/sqlite-manual.pdf",
                "chunk_index": 8,
                "semantic_score": 0.84,
                "ranking_score": 0.89,
                "quality_report": FakeQualityReport(97),
                "ranking": {
                    "semantic": 0.84,
                    "lexical": 1.0,
                    "quality": 0.97,
                    "authority": 1.0,
                    "completeness": 0.80,
                    "freshness": 0.50,
                    "diversity": 1.0,
                    "duplicate_penalty": 0.0,
                    "final_score": 0.89,
                },
            },
            {
                "text": "Aircraft hydraulic servicing procedures.",
                "source": "/notes/hydraulics.txt",
                "chunk_index": 1,
                "semantic_score": 0.91,
                "ranking_score": 0.42,
                "quality_report": FakeQualityReport(90),
                "ranking": {
                    "semantic": 0.91,
                    "lexical": 0.0,
                    "quality": 0.90,
                    "authority": 0.25,
                    "completeness": 0.40,
                    "freshness": 0.50,
                    "diversity": 1.0,
                    "duplicate_penalty": 0.0,
                    "final_score": 0.42,
                },
            },
        ]

        response = SearchService(
            self.database
        ).execute(
            "SQLite indexes",
            limit=2,
        )

        self.assertTrue(response.passed)

        self.assertEqual(
            response.results[0].file_path,
            "/docs/reference/sqlite-manual.pdf",
        )

        self.assertEqual(
            response.results[0].ranking_position,
            1,
        )

        self.assertAlmostEqual(
            response.results[0].score,
            0.89,
        )

        self.assertAlmostEqual(
            response.results[0].ranking_score,
            0.89,
        )

        self.assertAlmostEqual(
            response.results[0].semantic_score,
            0.84,
        )

        self.assertEqual(
            response.results[0].ranking["duplicate_penalty"],
            0.0,
        )

    @patch("knowledge_engine.search.service.QualityService")
    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_quality_report_survives_ranking(
        self,
        director_class,
        ranking_class,
        quality_service,
    ) -> None:
        report = FakeQualityReport(88)

        quality_service.validator.validate_chunk.return_value = report

        director_class.return_value.search.return_value = [
            {
                "score": 0.75,
                "source": "/docs/python.pdf",
                "chunk_index": 4,
                "text": "Python generators yield values lazily.",
            }
        ]

        def rank_results(
            query,
            results,
            limit=None,
        ):
            del query, limit

            candidate = dict(results[0])

            candidate["ranking_score"] = 0.81
            candidate["ranking"] = {
                "final_score": 0.81,
                "duplicate_penalty": 0.0,
            }

            return [candidate]

        ranking_class.return_value.rank.side_effect = rank_results

        response = SearchService(
            self.database
        ).execute(
            "Python generators",
            limit=1,
        )

        self.assertEqual(
            response.average_quality,
            88,
        )

        self.assertIs(
            response.results[0].quality,
            report,
        )

    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_empty_query_is_rejected(
        self,
        director_class,
        ranking_class,
    ) -> None:
        response = SearchService(
            self.database
        ).execute(
            "   ",
            limit=5,
        )

        self.assertFalse(response.passed)
        self.assertEqual(response.results, [])

        director_class.return_value.search.assert_not_called()
        ranking_class.return_value.rank.assert_not_called()

    @patch("knowledge_engine.search.service.RankingService")
    @patch("knowledge_engine.search.service.RetrievalDirector")
    def test_invalid_limit_is_rejected(
        self,
        director_class,
        ranking_class,
    ) -> None:
        response = SearchService(
            self.database
        ).execute(
            "SQLite",
            limit=0,
        )

        self.assertFalse(response.passed)
        self.assertEqual(response.results, [])

        director_class.return_value.search.assert_not_called()
        ranking_class.return_value.rank.assert_not_called()

    def test_tuple_candidate_normalization_remains_supported(self) -> None:
        with patch(
            "knowledge_engine.search.service.QualityService"
        ) as quality_service:
            quality_service.validator.validate_chunk.return_value = (
                FakeQualityReport(91)
            )

            candidate = SearchService._prepare_candidate(
                (
                    0.82,
                    "/docs/database.pdf",
                    7,
                    "Database indexes improve lookup performance.",
                )
            )

        self.assertEqual(
            candidate["source"],
            "/docs/database.pdf",
        )

        self.assertEqual(
            candidate["chunk_index"],
            7,
        )

        self.assertAlmostEqual(
            candidate["semantic_score"],
            0.82,
        )

        self.assertEqual(
            candidate["quality"],
            91,
        )

    def test_candidate_pool_expands_before_ranking(self) -> None:
        self.assertEqual(
            SearchService._candidate_limit(1),
            20,
        )

        self.assertEqual(
            SearchService._candidate_limit(5),
            20,
        )

        self.assertEqual(
            SearchService._candidate_limit(10),
            40,
        )


if __name__ == "__main__":
    unittest.main()
