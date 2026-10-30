from __future__ import annotations

import argparse
import json

from core.bounty_authorization import AuthorizationStore
from .airtable import AIRTABLE_PROFILE, create_airtable_authorization


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS reviewed bounty program profiles"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show")
    show.add_argument("profile", choices=["airtable"])

    apply = sub.add_parser("apply")
    apply.add_argument("profile", choices=["airtable"])
    apply.add_argument("--reviewer", required=True)
    apply.add_argument("--ttl", type=int, default=86400)
    apply.add_argument(
        "--approve",
        action="store_true",
        help="Required explicit confirmation to create an R5 authorization.",
    )

    args = parser.parse_args()

    if args.command == "show":
        print(json.dumps(AIRTABLE_PROFILE, indent=2, sort_keys=True))
        return 0

    if not args.approve:
        raise SystemExit(
            "Refusing to create authorization without --approve. "
            "Review it first with: python -m core.bounty_profiles show airtable"
        )

    auth_id = create_airtable_authorization(
        reviewer=args.reviewer,
        ttl=args.ttl,
        store=AuthorizationStore(),
    )

    print(json.dumps({
        "authorization_id": auth_id,
        "program": "airtable",
        "state": "created",
        "capabilities": AIRTABLE_PROFILE["capabilities"],
        "include": AIRTABLE_PROFILE["include"],
        "exclude": AIRTABLE_PROFILE["exclude"],
        "next_step": (
            "Create a bounty-agent session with root target "
            "staging.airtable.com. Creating the session does not run recon."
        ),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
