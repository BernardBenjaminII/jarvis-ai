from __future__ import annotations

import argparse

from knowledge_engine.chunking.builder import DocumentChunkBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Build document chunks")
    parser.add_argument("--db", required=True)
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    result = DocumentChunkBuilder(db).build_ready_documents(limit=args.limit)

    print("\nChunking complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
