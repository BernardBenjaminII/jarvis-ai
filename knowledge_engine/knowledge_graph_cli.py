from __future__ import annotations

import argparse

from knowledge_engine.knowledge_graph.builder import KnowledgeGraphBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


def cmd_build(args) -> None:
    db = KnowledgeDatabase(args.db)
    result = KnowledgeGraphBuilder(db).build(
        root_filter=args.root_filter,
        limit=args.limit,
    )

    print("\nKnowledge Graph build complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
            for path, error in value[:10]:
                print(f"  - {path}: {error}")
        else:
            print(f"{key}: {value}")


def cmd_stats(args) -> None:
    db = KnowledgeDatabase(args.db)

    with db.connect() as conn:
        print("\nNode types:")
        for row in conn.execute("""
            SELECT node_type, COUNT(*) AS count
            FROM graph_nodes
            GROUP BY node_type
            ORDER BY count DESC
        """):
            print(f"  {row['node_type']}: {row['count']}")

        print("\nEdge types:")
        for row in conn.execute("""
            SELECT relationship_type, COUNT(*) AS count
            FROM graph_edges
            GROUP BY relationship_type
            ORDER BY count DESC
        """):
            print(f"  {row['relationship_type']}: {row['count']}")


def cmd_find(args) -> None:
    db = KnowledgeDatabase(args.db)
    pattern = f"%{args.name.lower()}%"

    with db.connect() as conn:
        rows = conn.execute("""
            SELECT node_uuid, node_type, name, canonical_name, confidence
            FROM graph_nodes
            WHERE lower(name) LIKE ?
               OR lower(canonical_name) LIKE ?
            ORDER BY confidence DESC, name
            LIMIT ?
        """, (pattern, pattern, args.limit)).fetchall()

        for row in rows:
            print("=" * 80)
            print(f"Type      : {row['node_type']}")
            print(f"Name      : {row['name']}")
            print(f"Canonical : {row['canonical_name']}")
            print(f"Confidence: {row['confidence']}")
            print(f"UUID      : {row['node_uuid']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Knowledge Graph")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--db", required=True)
    build.add_argument("--root-filter", default=None)
    build.add_argument("--limit", type=int, default=None)
    build.set_defaults(func=cmd_build)

    stats = sub.add_parser("stats")
    stats.add_argument("--db", required=True)
    stats.set_defaults(func=cmd_stats)

    find = sub.add_parser("find")
    find.add_argument("--db", required=True)
    find.add_argument("--name", required=True)
    find.add_argument("--limit", type=int, default=20)
    find.set_defaults(func=cmd_find)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
