from __future__ import annotations

import argparse
from pathlib import Path

from core.capabilities.models import CapabilityContext

from knowledge_engine.capabilities.objects import ObjectCapability
from knowledge_engine.storage.database import KnowledgeDatabase


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--db", required=True)

    parser.add_argument("--root-filter")

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    context = CapabilityContext(
        root=Path(args.root_filter).expanduser().resolve()
        if args.root_filter
        else None,
        database=db,
    )

    result = ObjectCapability(
        dry_run=args.dry_run
    ).execute(context)

    print()

    print("Knowledge Object Builder complete:")

    for k, v in sorted(result.metrics.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
