from __future__ import annotations

import argparse

from knowledge_engine.concepts.builder import ConceptBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract concepts from document chunks")
    parser.add_argument("--db", required=True)
    parser.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    result = ConceptBuilder(db).build_ready_chunks(limit=args.limit)

    print("\nConcept extraction complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
