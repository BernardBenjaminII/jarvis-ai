from __future__ import annotations

import argparse
from pathlib import Path

from core.capabilities.models import CapabilityContext

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.capabilities.discovery import DiscoveryCapability


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--root", required=True)

    parser.add_argument("--db", required=True)

    parser.add_argument("--limit", type=int)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    context = CapabilityContext(
        root=Path(args.root),
        database=db,
    )

    result = DiscoveryCapability(
        limit=args.limit
    ).execute(context)

    print()

    print("Discovery complete:")

    for k, v in sorted(result.metrics.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
