"""Command-line interface for JARVIS Gen 2 missions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from core.executive.director import ExecutiveDirector


def default_database_path() -> Path:
    configured = os.getenv("JARVIS_MISSION_DB")
    if configured:
        return Path(configured).expanduser()
    return Path("runtime/missions/jarvis_missions.sqlite3")


def parse_context(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("--context must decode to a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis-gen2",
        description="JARVIS Gen 2 Executive Director and Mission Engine",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_database_path(),
        help="Mission SQLite database path",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    submit = commands.add_parser("submit", help="Create and run a mission")
    submit.add_argument("objective")
    submit.add_argument(
        "--context",
        help="JSON object containing mission context",
    )
    submit.add_argument(
        "--plan-only",
        action="store_true",
        help="Create the plan without executing it",
    )

    show = commands.add_parser("show", help="Show one mission")
    show.add_argument("mission_id")
    show.add_argument(
        "--events",
        action="store_true",
        help="Include lifecycle events",
    )

    list_command = commands.add_parser("list", help="List missions")
    list_command.add_argument("--status")
    list_command.add_argument("--limit", type=int, default=20)

    execute = commands.add_parser(
        "execute",
        help="Execute a previously planned mission",
    )
    execute.add_argument("mission_id")

    return parser


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    director = ExecutiveDirector(database_path=args.db)

    if args.command == "submit":
        mission = director.submit(
            args.objective,
            context=parse_context(args.context),
            execute=not args.plan_only,
        )
        print_json(mission.to_dict())
        return 0

    if args.command == "show":
        mission = director.get_mission(args.mission_id)
        data = mission.to_dict()
        if args.events:
            data["events"] = director.mission_events(args.mission_id)
        print_json(data)
        return 0

    if args.command == "list":
        missions = director.list_missions(
            status=args.status,
            limit=args.limit,
        )
        print_json([mission.to_dict() for mission in missions])
        return 0

    if args.command == "execute":
        mission = director.execute_mission(args.mission_id)
        print_json(mission.to_dict())
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
