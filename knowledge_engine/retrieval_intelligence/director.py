"""Retrieval Director for the JARVIS Knowledge Engine."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from knowledge_engine.retrieval_intelligence.filtering import (
    DEFAULT_MINIMUM_SIMILARITY,
    CandidateFilter,
    confidence_label,
)
from knowledge_engine.retrieval_intelligence.merger import CandidateMerger
from knowledge_engine.retrieval_intelligence.models import (
    ProviderDiagnostics,
    RetrievalCandidate,
    RetrievalDiagnostics,
)
from knowledge_engine.retrieval_intelligence.providers import (
    RetrievalProvider,
    VectorRetrievalProvider,
)


DEFAULT_PROVIDER_MULTIPLIER = 4
DEFAULT_MINIMUM_PROVIDER_LIMIT = 20


class RetrievalDirector:
    """Coordinate multiple retrievers and enforce retrieval policy."""

    def __init__(
        self,
        database: Any | None = None,
        *,
        providers: Iterable[RetrievalProvider] | None = None,
        minimum_similarity: float = DEFAULT_MINIMUM_SIMILARITY,
    ) -> None:
        configured = list(providers or [])

        if not configured:
            if database is None:
                raise ValueError(
                    "database is required when providers are not supplied."
                )

            configured = [
                VectorRetrievalProvider(database),
            ]

        self.providers = configured
        self.merger = CandidateMerger()
        self.filter = CandidateFilter(
            minimum_similarity=minimum_similarity
        )
        self.last_diagnostics: RetrievalDiagnostics | None = None

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve, merge, filter, diagnose, and return candidates."""

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("query must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        provider_limit = limit

        provider_groups: list[list[RetrievalCandidate]] = []
        provider_diagnostics: list[ProviderDiagnostics] = []

        for provider in self.providers:
            returned = provider.retrieve(
                normalized_query,
                limit=provider_limit,
            )

            accepted, rejected = self.filter.apply(returned)

            scores = [
                candidate.normalized_score
                for candidate in returned
            ]

            provider_diagnostics.append(
                ProviderDiagnostics(
                    provider=provider.name,
                    returned=len(returned),
                    accepted=len(accepted),
                    rejected=len(rejected),
                    highest_score=max(scores, default=0.0),
                    average_score=(
                        sum(scores) / len(scores)
                        if scores
                        else 0.0
                    ),
                )
            )

            # Merge the provider's complete result set before applying the
            # global threshold. This preserves cross-provider deduplication.
            provider_groups.append(returned)

        retrieved_count = sum(
            len(group)
            for group in provider_groups
        )

        merged = self.merger.merge(provider_groups)
        accepted, rejected = self.filter.apply(merged)

        accepted = accepted[:limit]

        accepted_scores = [
            candidate.normalized_score
            for candidate in accepted
        ]

        all_merged_scores = [
            candidate.normalized_score
            for candidate in merged
        ]

        self.last_diagnostics = RetrievalDiagnostics(
            query=normalized_query,
            requested_limit=limit,
            provider_count=len(self.providers),
            retrieved_candidates=retrieved_count,
            merged_candidates=len(merged),
            accepted_candidates=len(accepted),
            rejected_candidates=len(rejected),
            minimum_similarity=self.filter.minimum_similarity,
            highest_similarity=max(
                all_merged_scores,
                default=0.0,
            ),
            average_similarity=(
                sum(accepted_scores) / len(accepted_scores)
                if accepted_scores
                else 0.0
            ),
            confidence=confidence_label(accepted),
            providers=tuple(provider_diagnostics),
        )

        return [
            candidate.as_mapping()
            for candidate in accepted
        ]

    @staticmethod
    def _provider_limit(result_limit: int) -> int:
        """Return the candidate budget allocated to each provider."""

        return max(
            DEFAULT_MINIMUM_PROVIDER_LIMIT,
            result_limit * DEFAULT_PROVIDER_MULTIPLIER,
        )
