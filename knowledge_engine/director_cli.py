from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_engine.director.knowledge_director import KnowledgeDirector
from knowledge_engine.director.models import DirectorRequest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the JARVIS Knowledge Director."
    )

    parser.add_argument("intent")
    parser.add_argument("--source", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    request = DirectorRequest(
        intent=args.intent,
        source_path=Path(args.source) if args.source else None,
        query=args.query,
        metadata={"limit": args.limit},
    )

    response = KnowledgeDirector().handle(request)

    print()
    print("=" * 70)
    print("KNOWLEDGE DIRECTOR")
    print("=" * 70)
    print(f"Intent   : {response.intent}")
    print(f"Workflow : {response.workflow}")
    print(f"Passed   : {response.passed}")
    print(f"Message  : {response.message}")

    metadata = response.metadata or {}
    results = metadata.get("results", [])

    if metadata:
        print()
        print("Metadata")
        print("-" * 70)

        for key, value in metadata.items():
            if key == "results":
                continue
            print(f"{key}: {value}")

    if results:
        print()
        print("Results")
        print("-" * 70)

        for index, item in enumerate(results, start=1):
            # Supports both tuple results and dict results.
            if isinstance(item, dict):
                score = item.get("score", 0)
                file_path = item.get("file_path", "")
                chunk_index = item.get("chunk_index", "")
                text = item.get("text_preview", "")
            else:
                score, file_path, chunk_index, text = item

            print(f"{index}. Score : {float(score):.4f}")
            print(f"   File  : {file_path}")
            print(f"   Chunk : {chunk_index}")
            print()
            print(str(text)[:500])
            print()

    if response.errors:
        print()
        print("Errors")
        print("-" * 70)
        for error in response.errors:
            print(error)

    return 0 if response.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
