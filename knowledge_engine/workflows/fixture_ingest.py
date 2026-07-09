from __future__ import annotations

from pathlib import Path

from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.runner import WorkflowRunner

from knowledge_engine.workflows.stages.receiving import ReceivingStage
from knowledge_engine.workflows.stages.extraction import ExtractionStage

from knowledge_engine.workflows.core.simple_stages import (
    ChunkTextStage,
    MockEmbeddingStage,
    MockRegistryStage,
    MockRetrievalStage,
)


def build_fixture_ingest_workflow() -> WorkflowRunner:
    return WorkflowRunner(
        name="Fixture Knowledge Ingest Workflow",
        stages=[
            ReceivingStage(),
            ExtractionStage(),
            ChunkTextStage(),
            MockEmbeddingStage(),
            MockRegistryStage(),
            MockRetrievalStage(),
        ],
    )


def run_fixture_ingest(source_path: str | Path):
    context = KnowledgeContext(source_path=Path(source_path))
    workflow = build_fixture_ingest_workflow()
    return workflow.run(context)
