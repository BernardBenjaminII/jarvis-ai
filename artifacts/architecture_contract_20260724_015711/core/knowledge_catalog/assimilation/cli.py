from __future__ import annotations

import argparse
from pathlib import Path

from core.knowledge_catalog.assimilation.engine import (
    assimilate_file,
    assimilate_tree,
    migrate,
)


def cmd_file(args: argparse.Namespace) -> None:
    migrate()
    r = assimilate_file(Path(args.path))

    print("Assimilation Result")
    print("=" * 60)
    print(f"title       : {r.title}")
    print(f"domain      : {r.domain}")
    print(f"discipline  : {r.discipline}")
    print(f"subject     : {r.subject}")
    print(f"collection  : {r.collection_id}")
    print(f"confidence  : {r.confidence:.2f}")
    print(f"chars       : {r.content_chars}")
    print(f"evidence    : {r.evidence}")


def cmd_tree(args: argparse.Namespace) -> None:
    result = assimilate_tree(Path(args.root))
    print("[OK] Assimilation complete")
    for k, v in result.items():
        print(f"{k:<18} {v}")


def cmd_migrate(_: argparse.Namespace) -> None:
    migrate()
    print("[OK] Assimilation tables ready")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Knowledge Assimilation v1")
    sub = parser.add_subparsers(dest="command", required=True)

    p_migrate = sub.add_parser("migrate")
    p_migrate.set_defaults(func=cmd_migrate)

    p_file = sub.add_parser("file")
    p_file.add_argument("path")
    p_file.set_defaults(func=cmd_file)

    p_tree = sub.add_parser("tree")
    p_tree.add_argument("--root", default="/media/abdullah/JARVISDATA/Knowledge")
    p_tree.set_defaults(func=cmd_tree)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
