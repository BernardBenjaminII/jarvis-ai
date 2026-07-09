from __future__ import annotations

import argparse

from knowledge_engine.registry.builder import KnowledgeRegistryBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JARVIS Knowledge Registry")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--root-filter", default=None, help="Only register object paths matching this text")

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    builder = KnowledgeRegistryBuilder(db)

    result = builder.build(root_filter=args.root_filter)

    print("\nKnowledge Registry complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
