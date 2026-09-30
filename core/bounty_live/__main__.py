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

    prop = sub.add_parser("propose-httpx")
    prop.add_argument("task")

    lp = sub.add_parser("proposals")
    lp.add_argument("mission")
    lp.add_argument(
        "--state",
        choices=["proposed", "approved", "rejected"],
    )

    ap = sub.add_parser("approve")
    ap.add_argument("proposal")
    ap.add_argument("--reviewer", required=True)

    rp = sub.add_parser("reject")
    rp.add_argument("proposal")
    rp.add_argument("--reviewer", required=True)

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

    elif args.command == "propose-httpx":
        out = {
            "proposal_ids":
                store.propose_httpx_from_subfinder(args.task)
        }

    elif args.command == "proposals":
        out = {
            "proposals":
                store.proposals(args.mission, args.state)
        }

    elif args.command == "approve":
        out = {
            "task_id": store.approve_proposal(
                args.proposal,
                args.reviewer,
            )
        }

    elif args.command == "reject":
        store.reject_proposal(
            args.proposal,
            args.reviewer,
        )
        out = {"state": "rejected"}

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
