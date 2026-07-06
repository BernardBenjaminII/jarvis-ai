from __future__ import annotations

import argparse

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.validation.builder import KnowledgeValidationBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Knowledge Objects")
    parser.add_argument("--db", required=True)
    parser.add_argument("--root-filter", default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    result = KnowledgeValidationBuilder(db).build(root_filter=args.root_filter)

    print("\nKnowledge Validation complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
