from __future__ import annotations

from core.capabilities.registry import CapabilityRegistry
from core.capabilities.adapters import BuilderCapability

from knowledge_engine.chunking.builder import DocumentChunkBuilder
from knowledge_engine.embeddings.builder import ChunkEmbeddingBuilder
from knowledge_engine.hybrid_retrieval.index_builder import HybridIndexBuilder
from knowledge_engine.knowledge_graph.builder import KnowledgeGraphBuilder


def build_knowledge_registry(
    *,
    chunk_limit: int = 25,
    embedding_limit: int = 25,
    faiss_index_dir: str = "/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss",
) -> CapabilityRegistry:
    registry = CapabilityRegistry()

    registry.register(
        BuilderCapability(
            name="knowledge.chunking",
            description="Build chunks for resources ready for chunking",
            builder_cls=DocumentChunkBuilder,
            method_name="build_ready_documents",
            requires=set(),
            provides={"chunks"},
            order=600,
            kwargs={"limit": chunk_limit},
        )
    )

    registry.register(
        BuilderCapability(
            name="knowledge.embeddings",
            description="Embed pending chunks",
            builder_cls=ChunkEmbeddingBuilder,
            method_name="build_pending_embeddings",
            requires={"chunks"},
            provides={"embeddings"},
            order=700,
            kwargs={"limit": embedding_limit},
        )
    )

    registry.register(
        BuilderCapability(
            name="knowledge.faiss",
            description="Rebuild FAISS vector index",
            builder_cls=HybridIndexBuilder,
            method_name="rebuild",
            requires={"embeddings"},
            provides={"faiss"},
            order=800,
            kwargs={},
        )
    )

    registry.register(
        BuilderCapability(
            name="knowledge.graph",
            description="Build knowledge graph",
            builder_cls=KnowledgeGraphBuilder,
            method_name="build",
            requires=set(),
            provides={"graph"},
            order=900,
            kwargs={},
        )
    )

    return registry
