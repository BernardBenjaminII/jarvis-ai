"""Search workflow for the JARVIS Knowledge Director."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge_engine.director.models import DirectorResponse
from knowledge_engine.director.workflow import Workflow
from knowledge_engine.query_understanding import QueryUnderstandingService
from knowledge_engine.search.service import SearchService
from knowledge_engine.storage.database import KnowledgeDatabase


DEFAULT_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


class SearchWorkflow(Workflow):
    """Understand, retrieve, rank, and return knowledge evidence."""

    intent = "search"
    name = "Search"

    def run(self, request):
        """Execute the structured search workflow."""

        original_query = request.query.strip()

        if not original_query:
            return DirectorResponse(
                intent=request.intent,
                workflow=self.name,
                passed=False,
                message="Missing query.",
                errors=["Search query is required."],
            )

        try:
            understanding = QueryUnderstandingService().understand(
                original_query
            )
        except Exception as exc:
            return DirectorResponse(
                intent=request.intent,
                workflow=self.name,
                passed=False,
                message="Query understanding failed.",
                errors=[str(exc)],
            )

        database = KnowledgeDatabase(DEFAULT_DB)
        service = SearchService(database)

        try:
            limit = self._result_limit(
                request.metadata.get(
                    "limit",
                    5,
                )
            )

            response = service.execute(
                query=understanding.retrieval_query,
                limit=limit,
            )
        except Exception as exc:
            return DirectorResponse(
                intent=request.intent,
                workflow=self.name,
                passed=False,
                message="Search failed.",
                metadata={
                    "query_understanding": understanding.as_dict(),
                },
                errors=[str(exc)],
            )

        return DirectorResponse(
            intent=request.intent,
            workflow=self.name,
            passed=response.passed,
            message=response.message,
            metadata={
                "original_query": original_query,
                "retrieval_query": understanding.retrieval_query,
                "query_understanding": understanding.as_dict(),
                "result_count": len(response.results),
                "quality": response.average_quality,
                "results": response.results,
            },
        )

    @staticmethod
    def _result_limit(value: Any) -> int:
        """Normalize and validate the requested result limit."""

        try:
            limit = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Search limit must be an integer."
            ) from exc

        if limit <= 0:
            raise ValueError(
                "Search limit must be greater than zero."
            )

        return limit
