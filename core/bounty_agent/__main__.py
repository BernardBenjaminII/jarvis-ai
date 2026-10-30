from __future__ import annotations

import argparse
import json

from .engine import BountyAgent, BountyAgentError


def main():
    p = argparse.ArgumentParser(description="JARVIS Bounty Agent R6 - authorized recon and human-gated pursuit")
    p.add_argument("--db")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("authorization")
    c.add_argument("root_target")
    c.add_argument("--budget", type=int, default=100)

    r = sub.add_parser("run")
    r.add_argument("session")

    rep = sub.add_parser("report")
    rep.add_argument("session")

    ls = sub.add_parser("list")
    ls.add_argument("--limit", type=int, default=50)

    d = sub.add_parser("decide")
    d.add_argument("option")
    d.add_argument("decision", choices=["pursue", "hold", "reject"])
    d.add_argument("--reviewer", required=True)

    args = p.parse_args()
    agent = BountyAgent(path=args.db)

    if args.command == "create":
        out = {"session_id": agent.create(args.authorization, args.root_target, budget=args.budget)}
    elif args.command == "run":
        out = agent.run_recon(args.session)
    elif args.command == "report":
        out = agent.report(args.session)
    elif args.command == "list":
        out = {"sessions": agent.list_sessions(args.limit)}
    else:
        out = agent.decide(args.option, args.decision, args.reviewer)

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BountyAgentError as exc:
        raise SystemExit("Bounty agent error: " + str(exc)) from None
