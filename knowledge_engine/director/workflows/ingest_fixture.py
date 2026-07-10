from __future__ import annotations

from knowledge_engine.director.models import DirectorResponse
from knowledge_engine.director.workflow import Workflow
from knowledge_engine.workflows.fixture_ingest import run_fixture_ingest


class FixtureIngestWorkflow(Workflow):

    intent = "ingest_fixture"
    name = "Fixture Ingest"

    def run(self, request):

        context, report = run_fixture_ingest(
            request.source_path
        )

        return DirectorResponse(
            intent=request.intent,
            workflow=self.name,
            passed=context.ok and report.passed,
            message="Fixture ingest completed.",
            metadata={
                "chunks": len(context.chunks),
                "embeddings": len(context.embeddings),
                "registry_ids": len(context.registry_ids),
                "retrieval_verified": context.retrieval_verified,
            },
            errors=context.errors,
        )
