from __future__ import annotations

import argparse

from knowledge_engine.librarian.builder import LibrarianBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JARVIS Librarian catalog")
    parser.add_argument("--db", required=True)
    parser.add_argument("--root-filter", default=None)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    result = LibrarianBuilder(db).build(
        root_filter=args.root_filter,
        limit=args.limit,
    )

    print("\nLibrarian complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
            for path, error in value[:10]:
                print(f"  - {path}: {error}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
