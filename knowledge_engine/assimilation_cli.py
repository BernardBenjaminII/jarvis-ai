"""
Command-line interface for JARVIS controlled knowledge assimilation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from knowledge_engine.assimilation import (
    AssimilationDirector,
    AssimilationMission,
    AssimilationRunner,
    registered_handler_specs,
)
from knowledge_engine.storage.database import KnowledgeDatabase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run JARVIS Knowledge Assimilation"
    )

    parser.add_argument(
        "--db",
        required=True,
        help="Path to the JARVIS knowledge catalog SQLite database.",
    )

    actions = parser.add_mutually_exclusive_group(required=True)

    actions.add_argument(
        "--one-single-document",
        action="store_true",
        help="Run the legacy low-level single-document action.",
    )

    actions.add_argument(
        "--inventory",
        action="store_true",
        help="Show registry states and assigned assimilation handlers.",
    )

    actions.add_argument(
        "--handlers",
        action="store_true",
        help="Show registered object-type handler definitions.",
    )

    actions.add_argument(
        "--plan",
        action="store_true",
        help="Create a read-only object-type-aware assimilation plan.",
    )

    actions.add_argument(
        "--execute-plan",
        action="store_true",
        help=(
            "Reserved execution interface. Locked until Phase VI-B "
            "failure-safe handlers are implemented."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum objects selected by --plan. Default: 25.",
    )

    parser.add_argument(
        "--object-type",
        action="append",
        default=None,
        help=(
            "Restrict --plan to an object type. May be supplied more than once."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optionally write the result as JSON.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete result as JSON.",
    )

    return parser


def write_payload(
    payload: Any,
    destination: Path,
) -> Path:
    path = destination.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def print_inventory(rows: list[dict[str, Any]]) -> None:
    print()
    print("=" * 118)
    print("JARVIS GEN 2 — KNOWLEDGE OBJECT DISPATCH INVENTORY")
    print("=" * 118)
    print(
        f"{'OBJECT TYPE':<28}"
        f"{'LIFECYCLE':<18}"
        f"{'ASSIMILATION':<20}"
        f"{'COUNT':>8}  "
        f"{'HANDLER':<32}"
        f"{'READINESS':<12}"
    )
    print("-" * 118)

    total = 0

    for row in rows:
        total += row["total"]

        print(
            f"{row['object_type']:<28}"
            f"{row['lifecycle_state']:<18}"
            f"{row['assimilation_state']:<20}"
            f"{row['total']:>8}  "
            f"{row['handler_name']:<32}"
            f"{row['handler_readiness']:<12}"
        )

    print("-" * 118)
    print(f"TOTAL REGISTRY OBJECTS: {total:,}")
    print("=" * 118)


def print_handlers() -> None:
    print()
    print("=" * 96)
    print("JARVIS GEN 2 — ASSIMILATION HANDLER REGISTRY")
    print("=" * 96)

    for spec in registered_handler_specs():
        print(f"Object type : {spec.object_type}")
        print(f"Handler     : {spec.handler_name}")
        print(f"Kind        : {spec.handler_kind}")
        print(f"Readiness   : {spec.readiness.value}")
        print(f"Executable  : {spec.executable_in_phase_vi_a2}")
        print(f"Purpose     : {spec.description}")
        print("-" * 96)


def print_mission(mission: AssimilationMission) -> None:
    print()
    print("=" * 96)
    print("JARVIS GEN 2 — OBJECT-TYPE-AWARE ASSIMILATION MISSION")
    print("=" * 96)
    print(f"Mission ID         : {mission.mission_id}")
    print(f"Fingerprint        : {mission.fingerprint}")
    print(f"Status             : {mission.status.value}")
    print(f"Database           : {mission.database_path}")
    print(f"Requested limit    : {mission.requested_limit}")
    print(f"Object-type filter : {mission.requested_object_types or 'all queued types'}")
    print(f"Planned items      : {mission.total_items}")
    print(f"Dispatchable items : {mission.dispatchable_items}")
    print(f"Executable items   : {mission.executable_items}")

    print()
    print("Object-type counts:")

    if mission.object_type_counts:
        for object_type, count in mission.object_type_counts.items():
            print(f"  {object_type:<32} {count:>6}")
    else:
        print("  none")

    print()
    print("Handler counts:")

    if mission.handler_counts:
        for handler, count in mission.handler_counts.items():
            print(f"  {handler:<32} {count:>6}")
    else:
        print("  none")

    if mission.planning_notes:
        print()
        print("Planning notes:")

        for note in mission.planning_notes:
            print(f"  - {note}")

    print()
    print("-" * 96)

    if not mission.items:
        print("No queued registry objects were selected.")
    else:
        for item in mission.items:
            print(
                f"{item.sequence:>4}. "
                f"{item.object_type:<28} "
                f"{item.handler_name:<32} "
                f"{item.handler_readiness:<12}"
            )
            print(f"      UUID      : {item.object_uuid}")
            print(f"      Lifecycle : {item.lifecycle_state}")
            print(f"      Path      : {item.object_path}")

    print("=" * 96)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    db = KnowledgeDatabase(args.db)

    if args.one_single_document:
        runner = AssimilationRunner(db)
        result = runner.run_one_single_document()

        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print()
            print("Assimilation complete:")

            for key, value in result.items():
                print(f"{key}: {value}")

        if args.output:
            path = write_payload(result, args.output)
            print(f"JSON output: {path}")

        return

    if args.handlers:
        payload = [
            spec.to_dict()
            for spec in registered_handler_specs()
        ]

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print_handlers()

        if args.output:
            path = write_payload(payload, args.output)
            print(f"JSON output: {path}")

        return

    director = AssimilationDirector(db)

    if args.inventory:
        payload = director.inventory()

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print_inventory(payload)

        if args.output:
            path = write_payload(payload, args.output)
            print(f"JSON output: {path}")

        return

    mission = director.plan(
        limit=args.limit,
        object_types=args.object_type,
    )

    if args.execute_plan:
        director.execute(mission)

    payload = mission.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_mission(mission)

    if args.output:
        path = write_payload(payload, args.output)
        print(f"JSON output: {path}")


if __name__ == "__main__":
    main()
