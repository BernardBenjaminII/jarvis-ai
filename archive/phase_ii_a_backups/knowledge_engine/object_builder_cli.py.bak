from __future__ import annotations

import argparse
from knowledge_engine.objects.builder import build_objects


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Knowledge Object Builder")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--root-filter", default=None, help="Only build objects from paths matching this text")
    parser.add_argument("--dry-run", action="store_true", help="Preview object build without writing")

    args = parser.parse_args()

    counts = build_objects(
        db_path=args.db,
        root_filter=args.root_filter,
        dry_run=args.dry_run,
    )

    print("\nKnowledge Object Builder complete:")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
