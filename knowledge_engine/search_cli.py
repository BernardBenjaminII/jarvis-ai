from __future__ import annotations

import argparse

from knowledge_engine.retrieval.vector_search import VectorSearcher
from knowledge_engine.storage.database import KnowledgeDatabase


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--db", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    searcher = VectorSearcher(db)

    results = searcher.search(
        args.query,
        limit=args.limit,
    )

    for score, file_path, chunk, text in results:
        print("=" * 80)
        print(f"Score : {score:.3f}")
        print(f"Chunk : {chunk}")
        print(file_path)
        print()
        print(text[:600])


if __name__ == "__main__":
    main()
