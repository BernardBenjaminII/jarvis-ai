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

    args = parser.parse_args()

    request = DirectorRequest(
        intent=args.intent,
        source_path=Path(args.source) if args.source else None,
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

    if response.metadata:
        print()
        print("Metadata")
        print("-" * 70)
        for key, value in response.metadata.items():
            print(f"{key}: {value}")

    if response.errors:
        print()
        print("Errors")
        print("-" * 70)
        for error in response.errors:
            print(error)

    return 0 if response.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
