"""Service facade for the JARVIS Knowledge Ranking Engine."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from knowledge_engine.ranking import KnowledgeRanker, RankingWeights


class RankingService:
    """Application-facing service for retrieval-result reranking."""

    def __init__(
        self,
        *,
        weights: RankingWeights | None = None,
    ) -> None:
        self._ranker = KnowledgeRanker(weights=weights)

    def rank(
        self,
        query: str,
        results: Iterable[Any],
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return self._ranker.rank(
            query,
            results,
            limit=limit,
        )


def rank_search_results(
    query: str,
    results: Iterable[Any],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Rank search results through the canonical ranking service."""

    return RankingService().rank(
        query,
        results,
        limit=limit,
    )
