from __future__ import annotations

from pathlib import Path

from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.runner import WorkflowRunner

from knowledge_engine.workflows.stages.receiving import ReceivingStage
from knowledge_engine.workflows.stages.extraction import ExtractionStage

from knowledge_engine.workflows.stages.chunking import ChunkingStage
from knowledge_engine.workflows.stages.embeddings import EmbeddingStage
from knowledge_engine.workflows.stages.registry import RegistryStage
from knowledge_engine.workflows.stages.retrieval import RetrievalStage


def build_fixture_ingest_workflow() -> WorkflowRunner:
    return WorkflowRunner(
        name="Fixture Knowledge Ingest Workflow",
        stages=[
            ReceivingStage(),
            ExtractionStage(),
            ChunkingStage(),
            EmbeddingStage(),
            RegistryStage(),
            RetrievalStage("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite",),
        ],
    )


def run_fixture_ingest(source_path: str | Path):
    context = KnowledgeContext(source_path=Path(source_path))
    workflow = build_fixture_ingest_workflow()
    return workflow.run(context)
