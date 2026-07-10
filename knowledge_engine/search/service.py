"""Canonical production search service.

Phase V-B integrates explainable knowledge ranking into the production search
pipeline while preserving the public interfaces already used by the Knowledge
Director and command-line tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge_engine.services.quality import QualityService
from knowledge_engine.services.ranking import RankingService
from knowledge_engine.services.retrieval import RetrievalService


DEFAULT_CANDIDATE_MULTIPLIER = 4
DEFAULT_MINIMUM_CANDIDATES = 20


@dataclass
class SearchResult:
    """A final, explainably ranked knowledge-search result."""

    score: float

    file_path: str

    chunk_index: int

    text: str

    quality: object

    semantic_score: float = 0.0

    ranking_score: float = 0.0

    ranking: dict[str, float] | None = None

    ranking_position: int = 0


@dataclass
class SearchResponse:
    """Response returned by the canonical production search service."""

    passed: bool

    message: str

    query: str

    results: list[SearchResult]

    average_quality: int


class SearchService:
    """Canonical production search service.

    Responsibilities:

        • semantic candidate retrieval
        • quality validation
        • explainable reranking
        • source-diversity enforcement
        • final result construction
    """

    def __init__(self, database) -> None:

        self.retrieval = RetrievalService(database)

        self.ranking = RankingService()

    def execute(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:
        """Execute the ranked production search workflow."""

        normalized_query = query.strip()

        if not normalized_query:

            return SearchResponse(

                passed=False,

                message="Search query is required.",

                query=query,

                results=[],

                average_quality=100,

            )

        if limit <= 0:

            return SearchResponse(

                passed=False,

                message="Search limit must be greater than zero.",

                query=normalized_query,

                results=[],

                average_quality=100,

            )

        candidate_limit = self._candidate_limit(limit)

        raw_results = self.retrieval.search(

            query=normalized_query,

            limit=candidate_limit,

        )

        candidates = [

            self._prepare_candidate(raw_result)

            for raw_result in raw_results

        ]

        ranked_results = self.ranking.rank(

            normalized_query,

            candidates,

            limit=limit,

        )

        results: list[SearchResult] = []

        quality_scores: list[int] = []

        for position, ranked_result in enumerate(

            ranked_results,

            start=1,

        ):

            result = self._build_search_result(

                ranked_result,

                position=position,

            )

            results.append(result)

            quality_scores.append(

                self._quality_score(result.quality)

            )

        average = (

            round(

                sum(quality_scores)

                / len(quality_scores)

            )

            if quality_scores

            else 100

        )

        return SearchResponse(

            passed=True,

            message=f"{len(results)} ranked results returned.",

            query=normalized_query,

            results=results,

            average_quality=average,

        )

    @staticmethod
    def _candidate_limit(result_limit: int) -> int:
        """Return the retrieval-pool size used before final ranking."""

        return max(

            DEFAULT_MINIMUM_CANDIDATES,

            result_limit * DEFAULT_CANDIDATE_MULTIPLIER,

        )

    @staticmethod
    def _prepare_candidate(
        raw_result: Any,
    ) -> dict[str, Any]:
        """Normalize a retrieval result for the ranking engine.

        The production VectorSearcher currently returns four-item tuples:

            score, file_path, chunk_index, text

        Mapping results are also supported to preserve testability and allow
        the retrieval layer to evolve without another search-service rewrite.
        """

        if isinstance(raw_result, dict):

            semantic_score = raw_result.get(

                "semantic_score",

                raw_result.get(

                    "score",

                    0.0,

                ),

            )

            file_path = raw_result.get(

                "source",

                raw_result.get(

                    "file_path",

                    "",

                ),

            )

            chunk_index = raw_result.get(

                "chunk_index",

                raw_result.get(

                    "chunk_number",

                    0,

                ),

            )

            text = raw_result.get(

                "text",

                raw_result.get(

                    "content",

                    "",

                ),

            )

        else:

            try:

                (
                    semantic_score,
                    file_path,
                    chunk_index,
                    text,
                ) = raw_result

            except (TypeError, ValueError) as exc:

                raise ValueError(

                    "Retrieval results must be dictionaries or four-item "

                    "tuples in the form "

                    "(score, file_path, chunk_index, text)."

                ) from exc

        normalized_text = str(text or "")

        quality_report = (

            QualityService.validator.validate_chunk(

                normalized_text

            )

        )

        return {

            "text": normalized_text,

            "content": normalized_text,

            "source": str(file_path or ""),

            "file_path": str(file_path or ""),

            "chunk_index": SearchService._integer_value(

                chunk_index

            ),

            "score": SearchService._float_value(

                semantic_score

            ),

            "semantic_score": SearchService._float_value(

                semantic_score

            ),

            "quality": SearchService._quality_score(

                quality_report

            ),

            "quality_score": SearchService._quality_score(

                quality_report

            ),

            "quality_report": quality_report,

        }

    @staticmethod
    def _build_search_result(
        ranked_result: dict[str, Any],
        *,
        position: int,
    ) -> SearchResult:
        """Convert a ranked mapping into the public SearchResult model."""

        text = str(

            ranked_result.get(

                "text",

                ranked_result.get(

                    "content",

                    "",

                ),

            )

        )

        quality_report = ranked_result.get(

            "quality_report"

        )

        if quality_report is None:

            quality_report = (

                QualityService.validator.validate_chunk(

                    text

                )

            )

        semantic_score = SearchService._float_value(

            ranked_result.get(

                "semantic_score",

                ranked_result.get(

                    "score",

                    0.0,

                ),

            )

        )

        ranking_score = SearchService._float_value(

            ranked_result.get(

                "ranking_score",

                ranked_result.get(

                    "score",

                    semantic_score,

                ),

            )

        )

        ranking_breakdown = ranked_result.get(

            "ranking"

        )

        if not isinstance(ranking_breakdown, dict):

            ranking_breakdown = {}

        return SearchResult(

            score=ranking_score,

            file_path=str(

                ranked_result.get(

                    "source",

                    ranked_result.get(

                        "file_path",

                        "",

                    ),

                )

            ),

            chunk_index=SearchService._integer_value(

                ranked_result.get(

                    "chunk_index",

                    ranked_result.get(

                        "chunk_number",

                        0,

                    ),

                )

            ),

            text=text,

            quality=quality_report,

            semantic_score=semantic_score,

            ranking_score=ranking_score,

            ranking=ranking_breakdown,

            ranking_position=position,

        )

    @staticmethod
    def _quality_score(
        quality: Any,
    ) -> int:
        """Extract an integer quality score from a report or raw value."""

        value = getattr(

            quality,

            "score",

            quality,

        )

        try:

            return int(round(float(value)))

        except (TypeError, ValueError):

            return 0

    @staticmethod
    def _float_value(
        value: Any,
    ) -> float:
        """Safely convert a value to float."""

        try:

            return float(value)

        except (TypeError, ValueError):

            return 0.0

    @staticmethod
    def _integer_value(
        value: Any,
    ) -> int:
        """Safely convert a chunk identifier to integer."""

        try:

            return int(value)

        except (TypeError, ValueError):

            return 0
