from __future__ import annotations

import argparse

from knowledge_engine.chunking.builder import DocumentChunkBuilder
from knowledge_engine.doctor.checks import run_checks
from knowledge_engine.embeddings.builder import ChunkEmbeddingBuilder
from knowledge_engine.hybrid_retrieval.index_builder import HybridIndexBuilder
from knowledge_engine.orchestrator.pipeline import AssimilationPipeline
from knowledge_engine.orchestrator.stage import AssimilationStage
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the JARVIS Assimilation Pipeline")
    parser.add_argument("--db", required=True)
    parser.add_argument("--chunk-limit", type=int, default=25)
    parser.add_argument("--embedding-limit", type=int, default=25)
    parser.add_argument(
        "--faiss-index-dir",
        default="/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss",
    )

    args = parser.parse_args()
    db = KnowledgeDatabase(args.db)

    pipeline = AssimilationPipeline()

    pipeline.add_stage(
        AssimilationStage(
            name="Chunk Builder",
            description="Build document chunks",
            runner=lambda: DocumentChunkBuilder(db).build_ready_documents(
                limit=args.chunk_limit
            ),
        )
    )

    pipeline.add_stage(
        AssimilationStage(
            name="Embedding Builder",
            description="Generate embeddings",
            runner=lambda: ChunkEmbeddingBuilder(db).build_pending_embeddings(
                limit=args.embedding_limit
            ),
        )
    )

    pipeline.add_stage(
        AssimilationStage(
            name="FAISS Rebuild",
            description="Rebuild vector index from embedded chunks",
            runner=lambda: HybridIndexBuilder(
                db,
                index_dir=args.faiss_index_dir,
            ).rebuild(),
        )
    )

    def doctor_stage() -> dict:
        with db.connect() as conn:
            return run_checks(conn, faiss_dir=args.faiss_index_dir)

    pipeline.add_stage(
        AssimilationStage(
            name="Knowledge Doctor",
            description="Verify knowledge engine",
            runner=doctor_stage,
        )
    )

    report = pipeline.run()
    report.print()


if __name__ == "__main__":
    main()
