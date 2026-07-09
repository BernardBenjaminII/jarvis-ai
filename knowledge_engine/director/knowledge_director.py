from __future__ import annotations

from knowledge_engine.director.models import DirectorRequest, DirectorResponse
from knowledge_engine.workflows.fixture_ingest import run_fixture_ingest


class KnowledgeDirector:
    """
    High-level Knowledge Engine coordinator.

    The Director chooses which workflow should run.
    It does not perform extraction, chunking, embeddings, registry,
    graph, or retrieval work directly.
    """

    def handle(self, request: DirectorRequest) -> DirectorResponse:
        if request.intent == "ingest_fixture":
            return self._run_fixture_ingest(request)

        return DirectorResponse(
            intent=request.intent,
            workflow="none",
            passed=False,
            message=f"Unsupported intent: {request.intent}",
            errors=[f"No workflow registered for intent: {request.intent}"],
        )

    def _run_fixture_ingest(self, request: DirectorRequest) -> DirectorResponse:
        if request.source_path is None:
            return DirectorResponse(
                intent=request.intent,
                workflow="fixture_ingest",
                passed=False,
                message="Missing source_path.",
                errors=["source_path is required for ingest_fixture"],
            )

        context, report = run_fixture_ingest(request.source_path)

        return DirectorResponse(
            intent=request.intent,
            workflow=report.name,
            passed=context.ok and report.passed,
            message="Fixture ingest workflow completed."
            if context.ok and report.passed
            else "Fixture ingest workflow failed.",
            metadata={
                "content_type": context.content_type,
                "processor": context.processor,
                "processor_status": context.processor_status,
                "chunks": len(context.chunks),
                "chunk_strategy": context.chunk_strategy,
                "embeddings": len(context.embeddings),
                "registry_ids": len(context.registry_ids),
                "retrieval_verified": context.retrieval_verified,
            },
            errors=list(context.errors),
        )
