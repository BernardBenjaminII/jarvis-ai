import argparse
import json

from core.bounty_authorization import AuthorizationStore
from .engine import LiveMissionStore


def main():
    p = argparse.ArgumentParser(
        description="Jarvis bounty R5.1 reviewed live mission engine"
    )

    p.add_argument("--db")

    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("authorization")
    c.add_argument("--budget", type=int, default=100)

    q = sub.add_parser("queue")
    q.add_argument("mission")
    q.add_argument("capability", choices=["subfinder", "httpx"])
    q.add_argument("target")

    r = sub.add_parser("run")
    r.add_argument("task")

    rep = sub.add_parser("report")
    rep.add_argument("mission")

    args = p.parse_args()

    store = LiveMissionStore(path=args.db)

    if args.command == "create":
        out = {
            "mission_id": store.create(
                args.authorization,
                budget=args.budget,
            )
        }

    elif args.command == "queue":
        out = {
            "task_id": store.queue(
                args.mission,
                args.capability,
                args.target,
            )
        }

    elif args.command == "run":
        out = store.run(args.task)

    elif args.command == "report":
        out = store.report(args.mission)

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
