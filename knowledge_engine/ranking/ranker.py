"""Primary ranking orchestration for JARVIS knowledge results."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from knowledge_engine.ranking.duplicates import duplicate_penalty
from knowledge_engine.ranking.models import (
    RankingCandidate,
    RankingWeights,
)
from knowledge_engine.ranking.normalization import normalize_candidates
from knowledge_engine.ranking.scorer import calculate_breakdown


def _candidate_to_mapping(candidate: RankingCandidate) -> dict[str, Any]:
    original = candidate.original

    if isinstance(original, Mapping):
        output = dict(original)
    elif is_dataclass(original):
        output = asdict(original)
    elif hasattr(original, "__dict__"):
        output = dict(vars(original))
    else:
        output = {"result": original}

    output["ranking_score"] = (
        candidate.breakdown.final_score
        if candidate.breakdown is not None
        else 0.0
    )
    output["ranking"] = (
        candidate.breakdown.as_dict()
        if candidate.breakdown is not None
        else {}
    )

    # Preserve normalized fields when an upstream implementation uses
    # different field names.
    output.setdefault("text", candidate.text)
    output.setdefault("source", candidate.source)
    output.setdefault("chunk_index", candidate.chunk_index)
    output.setdefault("semantic_score", candidate.semantic_score)
    output.setdefault("quality", candidate.quality_score)

    return output


class KnowledgeRanker:
    """Explainable, deterministic reranker for retrieval candidates."""

    def __init__(
        self,
        *,
        weights: RankingWeights | None = None,
        duplicate_threshold: float = 0.82,
        maximum_duplicate_penalty: float = 0.30,
        source_repeat_penalty: float = 0.025,
    ) -> None:
        self.weights = weights or RankingWeights()
        self.duplicate_threshold = duplicate_threshold
        self.maximum_duplicate_penalty = maximum_duplicate_penalty
        self.source_repeat_penalty = source_repeat_penalty

    def rank_candidates(
        self,
        query: str,
        results: Iterable[Any],
        *,
        limit: int | None = None,
    ) -> list[RankingCandidate]:
        if not query or not query.strip():
            raise ValueError("A non-empty query is required for ranking.")

        if limit is not None and limit < 1:
            raise ValueError("Ranking limit must be at least 1.")

        candidates = normalize_candidates(results)

        for candidate in candidates:
            candidate.breakdown = calculate_breakdown(
                query=query,
                candidate=candidate,
                weights=self.weights,
            )

        candidates.sort(
            key=lambda candidate: (
                candidate.breakdown.final_score
                if candidate.breakdown is not None
                else 0.0
            ),
            reverse=True,
        )

        selected: list[RankingCandidate] = []
        remaining = list(candidates)
        source_counts: dict[str, int] = {}

        while remaining and (limit is None or len(selected) < limit):
            best_candidate: RankingCandidate | None = None
            best_adjusted_score = -1.0

            for candidate in remaining:
                penalty = duplicate_penalty(
                    candidate,
                    selected,
                    threshold=self.duplicate_threshold,
                    maximum_penalty=self.maximum_duplicate_penalty,
                )

                repeat_count = source_counts.get(candidate.source, 0)

                if candidate.source and repeat_count > 0:
                    penalty += min(
                        repeat_count * self.source_repeat_penalty,
                        0.10,
                    )

                breakdown = calculate_breakdown(
                    query=query,
                    candidate=candidate,
                    weights=self.weights,
                    duplicate_penalty=penalty,
                )
                candidate.breakdown = breakdown

                if breakdown.final_score > best_adjusted_score:
                    best_candidate = candidate
                    best_adjusted_score = breakdown.final_score

            if best_candidate is None:
                break

            remaining.remove(best_candidate)
            selected.append(best_candidate)

            if best_candidate.source:
                source_counts[best_candidate.source] = (
                    source_counts.get(best_candidate.source, 0) + 1
                )

        return selected

    def rank(
        self,
        query: str,
        results: Iterable[Any],
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        ranked = self.rank_candidates(query, results, limit=limit)
        return [_candidate_to_mapping(candidate) for candidate in ranked]


def rank_results(
    query: str,
    results: Iterable[Any],
    *,
    limit: int | None = None,
    weights: RankingWeights | None = None,
) -> list[dict[str, Any]]:
    """Convenience API for ranking retrieval results."""

    ranker = KnowledgeRanker(weights=weights)
    return ranker.rank(query, results, limit=limit)
