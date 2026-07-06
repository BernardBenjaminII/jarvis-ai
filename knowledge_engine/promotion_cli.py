from __future__ import annotations

import argparse

from knowledge_engine.promotion.executor import PromotionExecutor
from knowledge_engine.promotion.planner import PromotionPlanner
from knowledge_engine.storage.database import KnowledgeDatabase


def print_plan(items) -> None:
    print()
    print("PROMOTION PLAN")
    print("=" * 80)

    for item in items:
        print()
        print(f"Action : {item.action}")
        print(f"Title  : {item.title}")
        print(f"Type   : {item.object_type}")
        print(f"Subject: {item.subject}")
        print(f"From   : {item.source_path}")
        print(f"To     : {item.destination_path}")
        print(f"Reason : {item.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or execute JARVIS knowledge promotion")
    parser.add_argument("--db", required=True)
    parser.add_argument("--staging-root", required=True)
    parser.add_argument("--knowledge-root", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--execute", action="store_true")

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    planner = PromotionPlanner(db)

    items = planner.plan(
        staging_root=args.staging_root,
        knowledge_root=args.knowledge_root,
        limit=args.limit,
    )

    print_plan(items)

    print()
    print("Summary")
    print("-" * 40)
    print(f"items: {len(items)}")
    print(f"promote: {sum(1 for i in items if i.action == 'promote')}")
    print(f"skip: {sum(1 for i in items if i.action == 'skip')}")

    if not args.execute:
        print()
        print("Dry run only. Re-run with --execute to copy promoted resources.")
        return

    result = PromotionExecutor(db).execute(items)

    print()
    print("Promotion complete:")
    for key, value in result.items():
        if key.endswith("errors"):
            print(f"{key}: {len(value)}")
            for path, error in value[:10]:
                print(f"  - {path}: {error}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
