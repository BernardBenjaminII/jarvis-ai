from __future__ import annotations

import argparse

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.worker.worker import KnowledgeWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JARVIS Knowledge Worker")
    parser.add_argument("--db", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--limit", type=int, default=1)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    worker = KnowledgeWorker(db)

    if args.once:
        result = worker.run_once()
        print_result(result)
        return

    for _ in range(args.limit):
        result = worker.run_once()
        print_result(result)

        if result.get("processed", 0) == 0 and not result.get("deferred"):
            break


def print_result(result: dict) -> None:
    print("\nKnowledge Worker:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
