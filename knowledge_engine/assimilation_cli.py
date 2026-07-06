from __future__ import annotations

import argparse

from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JARVIS Knowledge Assimilation")
    parser.add_argument("--db", required=True)
    parser.add_argument("--one-single-document", action="store_true")

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    runner = AssimilationRunner(db)

    if args.one_single_document:
        result = runner.run_one_single_document()
    else:
        raise SystemExit("Choose an action, e.g. --one-single-document")

    print("\nAssimilation complete:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
