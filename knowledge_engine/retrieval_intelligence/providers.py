"""Retrieval-provider contracts and production vector provider."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from knowledge_engine.retrieval_intelligence.models import RetrievalCandidate
from knowledge_engine.retrieval_intelligence.normalization import (
    normalize_candidate,
)
from knowledge_engine.services.retrieval import RetrievalService


@runtime_checkable
class RetrievalProvider(Protocol):
    """Contract implemented by all Retrieval Intelligence providers."""

    name: str

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[RetrievalCandidate]:
        """Return normalized candidates for the supplied query."""


class VectorRetrievalProvider:
    """Adapter around the existing production RetrievalService."""

    name = "vector"

    def __init__(self, database: Any) -> None:
        self._service = RetrievalService(database)

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[RetrievalCandidate]:
        raw_results = self._service.search(
            query=query,
            limit=limit,
        )

        return [
            normalize_candidate(
                result,
                provider=self.name,
            )
            for result in raw_results
        ]


class StaticRetrievalProvider:
    """Deterministic provider used by tests and diagnostics."""

    def __init__(
        self,
        *,
        name: str,
        candidates: list[Any],
    ) -> None:
        self.name = name
        self._candidates = list(candidates)

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[RetrievalCandidate]:
        del query

        return [
            normalize_candidate(
                value,
                provider=self.name,
            )
            for value in self._candidates[:limit]
        ]
