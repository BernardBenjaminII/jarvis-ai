from __future__ import annotations

import argparse
from pathlib import Path

from core.capabilities.models import CapabilityContext

from knowledge_engine.capabilities.registry import RegistryCapability
from knowledge_engine.storage.database import KnowledgeDatabase


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--db", required=True)

    parser.add_argument("--root-filter")

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    context = CapabilityContext(
        root=(
            Path(args.root_filter).expanduser().resolve()
            if args.root_filter
            else None
        ),
        database=db,
    )

    result = RegistryCapability().execute(context)

    print()

    print("Knowledge Registry complete:")

    for key, value in sorted(result.metrics.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
