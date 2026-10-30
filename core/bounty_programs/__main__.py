from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from core.bounty_catalog.store import Catalog
from core.bounty_authorization import AuthorizationStore

from . import (
    ProgramSnapshot,
    ProgramStore,
    authorize_reviewed_program,
    hackerone_catalog_draft,
    normalize_assets,
    review_draft,
)


def parser():
    p = argparse.ArgumentParser(
        prog="python -m core.bounty_programs",
        description=(
            "Jarvis bounty program intake registry"
        ),
    )

    sub = p.add_subparsers(
        dest="command",
        required=True,
    )

    create = sub.add_parser(
        "create",
        help="Create reviewed program snapshot",
    )

    create.add_argument(
        "name",
    )

    create.add_argument(
        "--source",
        default="manual",
    )

    create.add_argument(
        "--handle",
        required=True,
    )

    create.add_argument(
        "--source-url",
        default="",
    )

    create.add_argument(
        "--include",
        action="append",
        default=[],
    )

    create.add_argument(
        "--exclude",
        action="append",
        default=[],
    )

    create.add_argument(
        "--rules",
        default="",
    )

    create.add_argument(
        "--source-material",
        required=True,
    )

    show = sub.add_parser(
        "show",
    )

    show.add_argument(
        "program_id",
    )

    sub.add_parser(
        "list",
    )

    acquire = sub.add_parser(
        "import-catalog-draft",
        help=(
            "Create a non-executable program draft "
            "from the authenticated HackerOne catalog"
        ),
    )

    acquire.add_argument(
        "handle",
    )

    acquire.add_argument(
        "--catalog-db",
        type=Path,
        default=(
            Path(
                os.environ.get(
                    "JARVIS_RUNTIME_ROOT",
                    str(
                        Path.home()
                        / ".local/share/jarvis"
                    ),
                )
            )
            / "bounty_catalog/r4.sqlite"
        ),
    )

    authorize = sub.add_parser(
        "authorize-reviewed",
        help=(
            "Create a live authorization from a "
            "human-reviewed ProgramSnapshot"
        ),
    )

    authorize.add_argument(
        "program_id",
    )

    authorize.add_argument(
        "--reviewer",
        required=True,
    )

    authorize.add_argument(
        "--capability",
        action="append",
        choices=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
        ],
        default=[],
        required=True,
    )

    authorize.add_argument(
        "--provider",
        action="append",
        choices=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        default=[],
        required=True,
    )

    authorize.add_argument(
        "--ttl",
        type=int,
        default=86400,
    )

    authorize.add_argument(
        "--note",
        default="",
    )

    review = sub.add_parser(
        "review-draft",
        help=(
            "Human-review a non-executable program draft "
            "and create a reviewed ProgramSnapshot"
        ),
    )

    review.add_argument(
        "draft_id",
    )

    review.add_argument(
        "--reviewer",
        required=True,
    )

    review.add_argument(
        "--include",
        action="append",
        default=[],
    )

    review.add_argument(
        "--exclude",
        action="append",
        default=[],
    )

    review.add_argument(
        "--acknowledge-policy-review",
        action="store_true",
    )

    show_draft = sub.add_parser(
        "show-draft",
    )

    show_draft.add_argument(
        "draft_id",
    )

    sub.add_parser(
        "list-drafts",
    )

    return p


def main():
    args = parser().parse_args()
    store = ProgramStore()

    if args.command == "create":
        assets = normalize_assets(
            in_scope=args.include,
            out_of_scope=args.exclude,
        )

        snapshot = (
            ProgramSnapshot.reviewed_input(
                source=args.source,
                handle=args.handle,
                name=args.name,
                source_url=args.source_url,
                assets=assets,
                rules_text=args.rules,
                source_material=(
                    args.source_material
                ),
            )
        )

        program_id = store.save(
            snapshot
        )

        print(
            json.dumps(
                {
                    "program_id":
                        program_id,
                    "snapshot":
                        snapshot.evidence(),
                },
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "show":
        print(
            json.dumps(
                store.get(
                    args.program_id
                ),
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "list":
        print(
            json.dumps(
                {
                    "programs":
                        store.list()
                },
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "import-catalog-draft":
        catalog = Catalog(
            args.catalog_db
        )

        draft = hackerone_catalog_draft(
            catalog,
            args.handle,
        )

        draft_id = store.save_draft(
            draft
        )

        print(
            json.dumps(
                {
                    "draft_id":
                        draft_id,
                    "draft":
                        draft.evidence(),
                },
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "authorize-reviewed":
        authorization_store = (
            AuthorizationStore()
        )

        authorization_id = (
            authorize_reviewed_program(
                program_store=store,
                authorization_store=(
                    authorization_store
                ),
                program_id=args.program_id,
                reviewer=args.reviewer,
                logical_capabilities=(
                    args.capability
                ),
                approved_providers=(
                    args.provider
                ),
                ttl=args.ttl,
                note=args.note,
            )
        )

        live_scope = (
            authorization_store.live_scope(
                authorization_id
            )
        )

        print(
            json.dumps(
                {
                    "authorization_id":
                        authorization_id,
                    "record":
                        authorization_store.get(
                            authorization_id
                        ),
                    "live_scope":
                        live_scope.evidence(),
                    "mission_created":
                        False,
                    "execution_started":
                        False,
                },
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "review-draft":
        program_id, snapshot = review_draft(
            store=store,
            draft_id=args.draft_id,
            reviewer=args.reviewer,
            include=args.include,
            exclude=args.exclude,
            acknowledge_policy_review=(
                args.acknowledge_policy_review
            ),
        )

        print(
            json.dumps(
                {
                    "program_id":
                        program_id,
                    "snapshot":
                        snapshot.evidence(),
                },
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "show-draft":
        print(
            json.dumps(
                store.get_draft(
                    args.draft_id
                ),
                indent=2,
                sort_keys=True,
            )
        )

    elif args.command == "list-drafts":
        print(
            json.dumps(
                {
                    "drafts":
                        store.list_drafts()
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
