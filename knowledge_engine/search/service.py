from __future__ import annotations

from dataclasses import dataclass

from knowledge_engine.services.quality import QualityService
from knowledge_engine.services.retrieval import RetrievalService


@dataclass
class SearchResult:

    score: float

    file_path: str

    chunk_index: int

    text: str

    quality: object


@dataclass
class SearchResponse:

    passed: bool

    message: str

    query: str

    results: list[SearchResult]

    average_quality: int


class SearchService:
    """
    Canonical production search service.

    Responsible for:

        • retrieval
        • quality validation
        • future ranking
        • future metadata filtering
        • future hybrid retrieval
    """

    def __init__(self, database):

        self.retrieval = RetrievalService(database)

    def execute(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:

        raw_results = self.retrieval.search(
            query=query,
            limit=limit,
        )

        results: list[SearchResult] = []

        quality_scores: list[int] = []

        for score, file_path, chunk_index, text in raw_results:

            report = QualityService.validator.validate_chunk(text)

            quality_scores.append(report.score)

            results.append(

                SearchResult(

                    score=score,

                    file_path=file_path,

                    chunk_index=chunk_index,

                    text=text,

                    quality=report,

                )

            )

        average = (
            round(sum(quality_scores) / len(quality_scores))
            if quality_scores
            else 100
        )

        return SearchResponse(

            passed=True,

            message=f"{len(results)} results returned.",

            query=query,

            results=results,

            average_quality=average,

        )
