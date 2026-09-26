import argparse
import json
from pathlib import Path

from .store import AuthorizationStore


def main():
    p = argparse.ArgumentParser(
        description="Jarvis bounty R5.1 reviewed authorization store"
    )

    p.add_argument("--db")

    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("program")
    c.add_argument("--include", action="append", required=True)
    c.add_argument("--exclude", action="append", default=[])
    c.add_argument(
        "--capability",
        action="append",
        choices=["subfinder", "httpx"],
        default=[],
    )
    c.add_argument("--reviewer", required=True)
    c.add_argument("--source-file", required=True)
    c.add_argument("--ttl", type=int, default=86400)
    c.add_argument("--note", default="")

    g = sub.add_parser("show")
    g.add_argument("authorization")

    r = sub.add_parser("revoke")
    r.add_argument("authorization")
    r.add_argument("--reason", default="")

    args = p.parse_args()

    store = AuthorizationStore(path=args.db)

    if args.command == "create":
        source = Path(args.source_file).read_text(
            encoding="utf-8"
        )

        capabilities = (
            args.capability
            if args.capability
            else ["subfinder", "httpx"]
        )

        auth = store.create(
            program=args.program,
            include=args.include,
            exclude=args.exclude,
            capabilities=capabilities,
            reviewer=args.reviewer,
            source_material=source,
            ttl=args.ttl,
            note=args.note,
        )

        out = {
            "authorization_id": auth,
            "record": store.get(auth),
        }

    elif args.command == "show":
        out = {
            "record": store.get(args.authorization),
            "events": store.events(args.authorization),
        }

    elif args.command == "revoke":
        store.revoke(
            args.authorization,
            reason=args.reason,
        )
        out = {"state": "revoked"}

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
