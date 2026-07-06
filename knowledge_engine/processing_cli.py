from __future__ import annotations

import argparse

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.processing.object_assimilation_stage import ObjectAssimilationStage


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Knowledge Object processing stages")
    parser.add_argument("--db", required=True)
    parser.add_argument("--one", action="store_true")

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    stage = ObjectAssimilationStage(db)

    if args.one:
        result = stage.run_one()
    else:
        raise SystemExit("Choose --one for the current milestone")

    print("\nProcessing complete:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
