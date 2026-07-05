from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_engine.hybrid_retrieval.index_builder import HybridIndexBuilder
from knowledge_engine.hybrid_retrieval.search import HybridSearcher
from knowledge_engine.storage.database import KnowledgeDatabase


DEFAULT_INDEX_DIR = "/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss"


def cmd_rebuild(args) -> None:
    db = KnowledgeDatabase(args.db)
    result = HybridIndexBuilder(db, args.index_dir).rebuild(limit=args.limit)

    print("\nFAISS index rebuild complete:")
    for key, value in result.items():
        print(f"{key}: {value}")


def cmd_search(args) -> None:
    db = KnowledgeDatabase(args.db)
    searcher = HybridSearcher(db, args.index_dir)

    results = searcher.search(
        query=args.query,
        limit=args.limit,
        vector_k=args.vector_k,
        vector_weight=args.vector_weight,
        metadata_weight=args.metadata_weight,
    )

    for result in results:
        print("=" * 100)
        print(f"Hybrid : {result.hybrid_score:.4f}")
        print(f"Vector : {result.vector_score:.4f}")
        print(f"Meta   : {result.metadata_score:.4f}")
        print(f"Title  : {result.resource_title}")
        print(f"Type   : {result.resource_type}")
        print(f"Subject: {result.subject}")
        print(f"Chunk  : {result.chunk_index}")
        print(f"File   : {result.file_path}")
        print()
        print(result.text[:900].strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS hybrid retrieval")
    sub = parser.add_subparsers(dest="command", required=True)

    rebuild = sub.add_parser("rebuild", help="Rebuild FAISS index from chunk_embeddings")
    rebuild.add_argument("--db", required=True)
    rebuild.add_argument("--index-dir", default=DEFAULT_INDEX_DIR)
    rebuild.add_argument("--limit", type=int, default=None)
    rebuild.set_defaults(func=cmd_rebuild)

    search = sub.add_parser("search", help="Hybrid search")
    search.add_argument("--db", required=True)
    search.add_argument("--index-dir", default=DEFAULT_INDEX_DIR)
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--vector-k", type=int, default=50)
    search.add_argument("--vector-weight", type=float, default=0.70)
    search.add_argument("--metadata-weight", type=float, default=0.30)
    search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
