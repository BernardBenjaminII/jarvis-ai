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
        choices=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
            # Legacy provider aliases remain accepted.
            "subfinder",
            "dnsx",
            "httpx",
        ],
        default=[],
        help=(
            "Authorized logical capability. "
            "Legacy provider names remain accepted."
        ),
    )
    c.add_argument(
        "--provider",
        action="append",
        choices=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        default=[],
        help="Approved concrete execution provider.",
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

        capability_aliases = {
            "subfinder": "subdomain_discovery",
            "dnsx": "dns_resolution",
            "httpx": "http_probe",
        }

        provider_aliases = {
            "subfinder": "subfinder",
            "dnsx": "dnsx",
            "httpx": "httpx",
        }

        requested = (
            args.capability
            if args.capability
            else [
                "subdomain_discovery",
                "http_probe",
            ]
        )

        logical_capabilities = sorted({
            capability_aliases.get(
                item,
                item,
            )
            for item in requested
        })

        providers = set(args.provider)

        # Preserve the old CLI behavior:
        # --capability subfinder/httpx also approves that
        # concrete provider.
        for item in requested:
            if item in provider_aliases:
                providers.add(
                    provider_aliases[item]
                )

        # Default provider selection for logical capabilities.
        if not providers:
            if (
                "subdomain_discovery"
                in logical_capabilities
            ):
                providers.add("subfinder")

            if (
                "dns_resolution"
                in logical_capabilities
            ):
                providers.add("dnsx")

            if "http_probe" in logical_capabilities:
                providers.add("httpx")

        auth = store.create(
            program=args.program,
            include=args.include,
            exclude=args.exclude,
            logical_capabilities=logical_capabilities,
            approved_providers=sorted(providers),
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
