from __future__ import annotations

import argparse
from pathlib import Path

from core.capabilities import CapabilityContext, CapabilityRunner
from core.capabilities.report import print_capability_report
from knowledge_engine.capabilities.registry import build_knowledge_registry
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JARVIS Knowledge capabilities")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--db", required=True)
    parser.add_argument("--chunk-limit", type=int, default=25)
    parser.add_argument("--embedding-limit", type=int, default=25)
    parser.add_argument(
        "--faiss-index-dir",
        default="/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss",
    )

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    registry = build_knowledge_registry(
        chunk_limit=args.chunk_limit,
        embedding_limit=args.embedding_limit,
        faiss_index_dir=args.faiss_index_dir,
    )

    context = CapabilityContext(
        root=Path(args.root).expanduser().resolve(),
        database=db,
        runtime={
            "faiss_index_dir": args.faiss_index_dir,
        },
    )

    results = CapabilityRunner(registry).run(context)
    print_capability_report(results)


if __name__ == "__main__":
    main()
