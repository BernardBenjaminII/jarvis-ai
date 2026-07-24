from __future__ import annotations

import argparse
from pathlib import Path

from core.semantic_digest.inspector import inspect_document
from core.semantic_digest.pipeline import process_document


def cmd_inspect(path: str) -> None:
    result = inspect_document(Path(path))
    print(result)


def cmd_digest(path: str) -> None:
    result = process_document(Path(path))

    print("Semantic Digest")
    print("=" * 60)
    for key in [
        "title",
        "file_type",
        "detected_type",
        "inspection_reason",
        "readable",
        "content_chars",
        "subject",
        "confidence",
        "assigned_by",
    ]:
        print(f"{key:<20} {result.get(key)}")

    print()
    print("Concepts:")
    for c in result.get("concepts", []):
        print(f"  - {c}")

    print()
    print("Keywords:")
    for k in result.get("keywords", []):
        print(f"  - {k}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Semantic Digest CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("path")

    p_digest = sub.add_parser("digest")
    p_digest.add_argument("path")

    args = parser.parse_args()

    if args.command == "inspect":
        cmd_inspect(args.path)
    elif args.command == "digest":
        cmd_digest(args.path)


if __name__ == "__main__":
    main()
