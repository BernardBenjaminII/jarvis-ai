from __future__ import annotations

import argparse

from knowledge_engine.membership.builder import KnowledgeMembershipBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Knowledge Object membership graph")
    parser.add_argument("--db", required=True)
    parser.add_argument("--root-filter", default=None)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    result = KnowledgeMembershipBuilder(db).build(
        root_filter=args.root_filter,
        limit=args.limit,
    )

    print(f"members_built: {result['members_built']}")

    for key, value in sorted(
        result["member_counts"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
