"""
Command-line interface for persistent JARVIS knowledge assimilation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from knowledge_engine.assimilation import (
    AssimilationDirector,
    AssimilationExecutionLockedError,
    AssimilationMission,
    AssimilationRunner,
    MissionNotFoundError,
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
        help="Process one eligible document through the safe runner.",
    )
    actions.add_argument(
        "--inventory",
        action="store_true",
        help="Show registry states and assigned handlers.",
    )
    actions.add_argument(
        "--handlers",
        action="store_true",
        help="Show registered assimilation handlers.",
    )
    actions.add_argument(
        "--plan",
        action="store_true",
        help="Create and persist a read-only mission.",
    )
    actions.add_argument(
        "--execute-plan",
        action="store_true",
        help="Create, persist, and execute a mission.",
    )
    actions.add_argument(
        "--resume-mission",
        metavar="MISSION_ID",
        help="Resume a persistent paused or interrupted mission.",
    )
    actions.add_argument(
        "--mission-status",
        metavar="MISSION_ID",
        help="Show one persistent mission and its item checkpoints.",
    )
    actions.add_argument(
        "--mission-history",
        action="store_true",
        help="Show recent persistent missions.",
    )
    actions.add_argument(
        "--recover-stale",
        action="store_true",
        help="Recover stale document processing claims.",
    )
    actions.add_argument(
        "--requeue-failed",
        action="store_true",
        help="Requeue eligible failed document jobs.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum planned, listed, or requeued objects. Default: 25.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help=(
            "Maximum mission items to attempt during this invocation. "
            "Remaining items cause the mission to pause."
        ),
    )
    parser.add_argument(
        "--object-type",
        action="append",
        default=None,
        help="Restrict planning to an object type. Repeat as needed.",
    )
    parser.add_argument(
        "--status-filter",
        default=None,
        help="Restrict --mission-history to a mission status.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue after document failure or blocked execution.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Default document retry limit. Default: 3.",
    )
    parser.add_argument(
        "--stale-minutes",
        type=int,
        default=30,
        help="Processing age considered stale. Default: 30 minutes.",
    )
    parser.add_argument(
        "--reset-attempts",
        action="store_true",
        help="Reset retry counts while explicitly requeuing failures.",
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
        help="Print complete JSON output.",
    )

    return parser


def write_payload(payload: Any, destination: Path) -> Path:
    path = destination.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def print_mission(mission: AssimilationMission) -> None:
    payload = mission.to_dict()
    summary = payload["summary"]

    print()
    print("=" * 100)
    print("JARVIS GEN 2 — PERSISTENT ASSIMILATION MISSION")
    print("=" * 100)
    print(f"Mission ID       : {mission.mission_id}")
    print(f"Status           : {mission.status.value}")
    print(f"Fingerprint      : {mission.fingerprint}")
    print(f"Created          : {mission.created_at}")
    print(f"Started          : {mission.started_at}")
    print(f"Paused           : {mission.paused_at}")
    print(f"Completed        : {mission.completed_at}")
    print(f"Total items      : {summary['total_items']}")
    print(f"Remaining items  : {summary['remaining_items']}")
    print(f"Processed        : {summary['processed']}")
    print(f"Failed           : {summary['failed']}")
    print(f"Skipped          : {summary['skipped']}")
    print(f"Blocked          : {summary['blocked']}")
    print("-" * 100)

    for item in mission.items:
        print(
            f"{item.sequence:>4}. "
            f"{item.status.value:<12} "
            f"{item.object_type:<26} "
            f"{item.object_uuid}"
        )
        print(f"      Handler: {item.handler_name}")
        print(f"      Path   : {item.object_path}")

        if item.message:
            print(f"      Note   : {item.message}")

    print("=" * 100)


def print_history(rows: list[dict[str, Any]]) -> None:
    print()
    print("=" * 120)
    print("JARVIS GEN 2 — ASSIMILATION MISSION HISTORY")
    print("=" * 120)
    print(
        f"{'MISSION ID':<42}"
        f"{'STATUS':<12}"
        f"{'TOTAL':>7}"
        f"{'DONE':>7}"
        f"{'FAIL':>7}"
        f"{'PAUSED/CHECKPOINT':>24}"
    )
    print("-" * 120)

    for row in rows:
        print(
            f"{row['mission_id']:<42}"
            f"{row['status']:<12}"
            f"{row['total_items']:>7}"
            f"{row['processed']:>7}"
            f"{row['failed']:>7}"
            f"{str(row['last_checkpoint_at']):>24}"
        )

    print("=" * 120)


def emit(
    *,
    payload: Any,
    args: argparse.Namespace,
    text_printer: Any | None = None,
) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif text_printer is not None:
        text_printer()

    if args.output:
        path = write_payload(payload, args.output)
        print(f"JSON output: {path}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.max_items is not None and args.max_items < 1:
        parser.error("--max-items must be at least 1")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be at least 1")
    if args.stale_minutes < 1:
        parser.error("--stale-minutes must be at least 1")

    db = KnowledgeDatabase(args.db)
    runner = AssimilationRunner(
        db,
        default_max_attempts=args.max_attempts,
    )
    director = AssimilationDirector(
        db,
        runner=runner,
    )

    try:
        if args.one_single_document:
            result = runner.run_one_single_document()
            emit(
                payload=result,
                args=args,
                text_printer=lambda: print(
                    json.dumps(result, indent=2, sort_keys=True)
                ),
            )
            return 0 if not result.get("failed") else 1

        if args.recover_stale:
            result = runner.recover_stale_processing(
                stale_after_minutes=args.stale_minutes,
            )
            emit(
                payload=result,
                args=args,
                text_printer=lambda: print(
                    json.dumps(result, indent=2, sort_keys=True)
                ),
            )
            return 0

        if args.requeue_failed:
            result = runner.requeue_failed_documents(
                limit=args.limit,
                reset_attempts=args.reset_attempts,
            )
            emit(
                payload=result,
                args=args,
                text_printer=lambda: print(
                    json.dumps(result, indent=2, sort_keys=True)
                ),
            )
            return 0

        if args.handlers:
            payload = [
                spec.to_dict()
                for spec in registered_handler_specs()
            ]
            emit(
                payload=payload,
                args=args,
                text_printer=lambda: print(
                    json.dumps(payload, indent=2, sort_keys=True)
                ),
            )
            return 0

        if args.inventory:
            payload = director.inventory()
            emit(
                payload=payload,
                args=args,
                text_printer=lambda: print(
                    json.dumps(payload, indent=2, sort_keys=True)
                ),
            )
            return 0

        if args.mission_history:
            payload = director.history(
                limit=args.limit,
                status=args.status_filter,
            )
            emit(
                payload=payload,
                args=args,
                text_printer=lambda: print_history(payload),
            )
            return 0

        if args.mission_status:
            mission = director.load_mission(args.mission_status)
            payload = {
                "mission": mission.to_dict(),
                "item_checkpoints": director.mission_store.mission_items(
                    args.mission_status
                ),
            }
            emit(
                payload=payload,
                args=args,
                text_printer=lambda: print_mission(mission),
            )
            return 0

        if args.resume_mission:
            mission = director.resume(
                args.resume_mission,
                stop_on_error=not args.continue_on_error,
                max_items=args.max_items,
                recover_stale_minutes=args.stale_minutes,
            )
            emit(
                payload=mission.to_dict(),
                args=args,
                text_printer=lambda: print_mission(mission),
            )
            return 1 if mission.failed or mission.blocked else 0

        if args.plan:
            mission = director.plan(
                limit=args.limit,
                object_types=args.object_type,
                persist=True,
            )
            emit(
                payload=mission.to_dict(),
                args=args,
                text_printer=lambda: print_mission(mission),
            )
            return 0

        if args.execute_plan:
            mission = director.plan_and_execute(
                limit=args.limit,
                object_types=args.object_type,
                stop_on_error=not args.continue_on_error,
                max_items=args.max_items,
            )
            emit(
                payload=mission.to_dict(),
                args=args,
                text_printer=lambda: print_mission(mission),
            )
            return 1 if mission.failed or mission.blocked else 0

    except AssimilationExecutionLockedError as exc:
        print(f"EXECUTION LOCKED: {exc}", file=sys.stderr)
        return 2
    except MissionNotFoundError as exc:
        print(f"MISSION NOT FOUND: {exc}", file=sys.stderr)
        return 2

    parser.error("No assimilation action selected")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
