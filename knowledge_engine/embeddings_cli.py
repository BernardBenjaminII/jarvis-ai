from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_engine.embeddings.engine import EmbeddingEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local embeddings for document chunks.")
    parser.add_argument(
        "--db",
        required=True,
        help="Path to JARVIS knowledge SQLite database.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of chunks to embed.",
    )

    args = parser.parse_args()

    result = EmbeddingEngine(Path(args.db)).build_missing(limit=args.limit)

    print("Embedding build complete")
    print(f"Model    : {result['model']}")
    print(f"Embedded : {result['embedded']}")
    print(f"Skipped  : {result['skipped']}")


if __name__ == "__main__":
    main()
