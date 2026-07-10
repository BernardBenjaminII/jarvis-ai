"""Application-facing Query Understanding service."""

from __future__ import annotations

from knowledge_engine.query_understanding.analyzer import QueryAnalyzer
from knowledge_engine.query_understanding.models import QueryUnderstanding


class QueryUnderstandingService:
    """Stable service facade for structured query analysis."""

    def __init__(
        self,
        analyzer: QueryAnalyzer | None = None,
    ) -> None:
        self._analyzer = analyzer or QueryAnalyzer()

    def understand(
        self,
        query: str,
    ) -> QueryUnderstanding:
        """Return a structured interpretation of the query."""

        return self._analyzer.analyze(query)


def understand_query(
    query: str,
) -> QueryUnderstanding:
    """Convenience API for one-shot query understanding."""

    return QueryUnderstandingService().understand(query)
