from __future__ import annotations

import argparse
from knowledge_engine.classification.classifier import classify_discovered


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS knowledge classification engine")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--root-filter", default=None, help="Only classify paths matching this text")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for testing")

    args = parser.parse_args()

    counts = classify_discovered(
        db_path=args.db,
        root_filter=args.root_filter,
        limit=args.limit,
    )

    print("\nClassification complete:")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
