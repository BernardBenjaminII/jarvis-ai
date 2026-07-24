from __future__ import annotations

import argparse
from pathlib import Path

from core.knowledge_catalog.collections import print_collections, upsert_collections
from core.knowledge_catalog.backfill import main as semantic_backfill
from core.knowledge_catalog.search import search_catalog
from core.knowledge_catalog.registrar import register_file, register_tree
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.database import connect, migrate
from core.knowledge_catalog.repository import CatalogRepository
from core.knowledge_catalog.service import initialize_catalog


def cmd_init(args: argparse.Namespace) -> None:
    stats = initialize_catalog(Path(args.db))
    print("[OK] Knowledge Catalog initialized")
    for key, value in stats.items():
        print(f"{key:<12} {value}")


def cmd_stats(args: argparse.Namespace) -> None:
    migrate(Path(args.db))
    with connect(Path(args.db)) as conn:
        repo = CatalogRepository(conn)
        stats = repo.stats()
        collections = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]

    print("Knowledge Catalog Stats")
    print("-----------------------")
    for key, value in stats.items():
        print(f"{key:<12} {value}")
    print(f"{'collections':<12} {collections}")


def cmd_topics(args: argparse.Namespace) -> None:
    migrate(Path(args.db))
    with connect(Path(args.db)) as conn:
        rows = conn.execute("SELECT path, desired_depth FROM topics ORDER BY path").fetchall()

    for row in rows:
        print(f"{row['path']:<45} {row['desired_depth']}")


def cmd_sources(args: argparse.Namespace) -> None:
    migrate(Path(args.db))
    with connect(Path(args.db)) as conn:
        rows = conn.execute("SELECT name, trust_tier, source_type FROM sources ORDER BY trust_tier, name").fetchall()

    for row in rows:
        print(f"tier={row['trust_tier']}  {row['name']:<24} {row['source_type']}")


def cmd_collections_build(args: argparse.Namespace) -> None:
    count = upsert_collections(Path(args.db))
    print(f"[OK] Collections discovered/updated: {count}")


def cmd_collections_list(args: argparse.Namespace) -> None:
    print_collections(Path(args.db))


def cmd_semantic_backfill(args: argparse.Namespace) -> None:
    semantic_backfill()


def cmd_search(args: argparse.Namespace) -> None:
    rows = search_catalog(args.query, limit=args.limit)

    print("=" * 80)
    print(f"JARVIS KNOWLEDGE CATALOG SEARCH: {args.query}")
    print("=" * 80)

    if not rows:
        print("No catalog matches.")
        return

    for row in rows:
        print(f"{row['subject']:<25} {row['confidence']:.2f} {row['file_path']}")

def cmd_register_file(args: argparse.Namespace) -> None:
    result = register_file(Path(args.path))
    print("[OK] Registered file")
    print(f"title   : {result['title']}")
    print(f"subject : {result.get('subject')}")
    print(f"concepts: {', '.join(result.get('concepts', []))}")
    print(f"keywords: {', '.join(result.get('keywords', []))}")


def cmd_register_tree(args: argparse.Namespace) -> None:
    result = register_tree(Path(args.root))
    print("[OK] Registered tree")
    print(f"registered: {result['registered']}")
    print(f"skipped   : {result['skipped']}")

def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Knowledge Catalog")
    parser.add_argument("--db", default=str(DEFAULT_CATALOG_DB))

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.set_defaults(func=cmd_init)

    p_stats = sub.add_parser("stats")
    p_stats.set_defaults(func=cmd_stats)

    p_topics = sub.add_parser("topics")
    p_topics.set_defaults(func=cmd_topics)

    p_sources = sub.add_parser("sources")
    p_sources.set_defaults(func=cmd_sources)

    p_col_build = sub.add_parser("collections-build")
    p_col_build.set_defaults(func=cmd_collections_build)

    p_col_list = sub.add_parser("collections-list")
    p_col_list.set_defaults(func=cmd_collections_list)

    p_semantic = sub.add_parser("semantic-backfill")
    p_semantic.set_defaults(func=cmd_semantic_backfill)

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=25)
    p_search.set_defaults(func=cmd_search)

    p_reg_file = sub.add_parser("register-file")
    p_reg_file.add_argument("path")
    p_reg_file.set_defaults(func=cmd_register_file)

    p_reg_tree = sub.add_parser("register-tree")
    p_reg_tree.add_argument("--root", default="/media/abdullah/JARVISDATA/Knowledge")
    p_reg_tree.set_defaults(func=cmd_register_tree)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
