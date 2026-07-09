from __future__ import annotations

from pathlib import Path

from knowledge_engine.director.models import DirectorResponse
from knowledge_engine.director.workflow import Workflow
from knowledge_engine.services.retrieval import RetrievalService
from knowledge_engine.storage.database import KnowledgeDatabase


DEFAULT_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


class SearchWorkflow(Workflow):

    intent = "search"
    name = "Search"

    def run(self, request):

        query = request.query.strip()

        if not query:
            return DirectorResponse(
                intent=request.intent,
                workflow=self.name,
                passed=False,
                message="Missing query.",
                errors=["Search query is required."],
            )

        database = KnowledgeDatabase(DEFAULT_DB)
        service = RetrievalService(database)

        limit = int(request.metadata.get("limit", 5))

        try:
            results = service.search(
                query=query,
                limit=limit,
            )

        except Exception as exc:
            return DirectorResponse(
                intent=request.intent,
                workflow=self.name,
                passed=False,
                message="Search failed.",
                errors=[str(exc)],
            )

        return DirectorResponse(
            intent=request.intent,
            workflow=self.name,
            passed=True,
            message=f"{len(results)} results returned.",
            metadata={
                "query": query,
                "result_count": len(results),
                "results": results,
            },
        )
