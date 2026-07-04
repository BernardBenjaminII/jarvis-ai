from __future__ import annotations

import argparse

from knowledge_engine.embeddings.builder import ChunkEmbeddingBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Build chunk embeddings")
    parser.add_argument("--db", required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--min-chars", type=int, default=200)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    result = ChunkEmbeddingBuilder(db).build_pending_embeddings(
        limit=args.limit,
        min_chars=args.min_chars,
    )

    print("\nEmbedding complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
            for item, error in value[:10]:
                print(f"  - {item}: {error}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
