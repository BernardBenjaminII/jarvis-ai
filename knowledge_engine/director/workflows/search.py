from __future__ import annotations

from pathlib import Path

from knowledge_engine.director.models import DirectorResponse
from knowledge_engine.director.workflow import Workflow

from knowledge_engine.search.service import SearchService

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

        service = SearchService(database)

        try:

            response = service.execute(

                query=query,

                limit=int(
                    request.metadata.get(
                        "limit",
                        5,
                    )
                ),

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

            passed=response.passed,

            message=response.message,

            metadata={

                "query": response.query,

                "result_count": len(response.results),

                "quality": response.average_quality,

                "results": response.results,

            },

        )
