"""
JARVIS R9.10B

Analysis-only program review packet.

Purpose:
- convert R9.9 ranking output into a human review packet
- preserve HackerOne catalog provenance
- surface policy evidence and review requirements
- never create authorization
- never execute tools
- never infer structured scope

The existing R9.0B -> R9.0C -> R9.0D chain remains
authoritative for drafts, reviewed scope, and authorization.
"""

from __future__ import annotations

import re
from typing import Any

from core.bounty_catalog.opportunity import (
    latest_raw_programs,
    score_program,
)


def _policy_excerpts(
    policy: str,
    terms: tuple[str, ...],
    *,
    limit: int = 8,
    radius: int = 180,
) -> list[str]:
    found = []
    seen = set()

    lower = policy.casefold()

    for term in terms:
        start = 0

        while True:
            pos = lower.find(
                term.casefold(),
                start,
            )

            if pos < 0:
                break

            lo = max(
                0,
                pos - radius,
            )

            hi = min(
                len(policy),
                pos + len(term) + radius,
            )

            excerpt = re.sub(
                r"\s+",
                " ",
                policy[lo:hi],
            ).strip()

            key = excerpt.casefold()

            if key not in seen:
                seen.add(key)
                found.append(excerpt)

            if len(found) >= limit:
                return found

            start = pos + len(term)

    return found


def _find_raw_program(
    catalog,
    handle: str,
) -> dict[str, Any]:
    handle = str(handle).strip()

    if not handle:
        raise ValueError(
            "Program handle is required"
        )

    for item in latest_raw_programs(
        catalog
    ):
        attributes = item.get(
            "attributes"
        )

        if not isinstance(
            attributes,
            dict,
        ):
            continue

        if (
            attributes.get("handle")
            == handle
        ):
            return attributes

    raise KeyError(
        f"Program not found in latest catalog run: {handle}"
    )


def program_review_packet(
    catalog,
    handle: str,
) -> dict[str, Any]:
    """
    Build a human-review packet from already-stored catalog data.

    No network traffic.
    No ProgramSnapshot.
    No authorization.
    No execution tasks.
    """

    raw = _find_raw_program(
        catalog,
        handle,
    )

    catalog_record = catalog.review_record(
        handle,
        source="hackerone-api",
    )

    opportunity = score_program(
        raw
    )

    policy = str(
        raw.get("policy")
        or ""
    )

    signals = opportunity[
        "policy_signals"
    ]

    automation_evidence = (
        signals.get(
            "automation_permit_evidence",
            [],
        )
        + signals.get(
            "automation_restrict_evidence",
            [],
        )
    )

    automation_evidence = list(
        dict.fromkeys(
            automation_evidence
        )
    )

    scope_evidence = _policy_excerpts(
        policy,
        (
            "in scope",
            "out of scope",
            "scope",
            "authorized assets",
            "authorized asset",
        ),
    )

    account_evidence = _policy_excerpts(
        policy,
        (
            "test account",
            "testing account",
            "account you own",
            "accounts you own",
            "hackerone username",
            "researcher account",
        ),
    )

    rate_limit_evidence = _policy_excerpts(
        policy,
        (
            "requests per second",
            "requests per minute",
            "requests per hour",
            "requests per day",
            "rate-limit",
            "rate limit",
            "automated tooling",
            "automated testing",
        ),
    )

    third_party_evidence = _policy_excerpts(
        policy,
        (
            "third party",
            "third-party",
            "customer",
            "customers",
            "vendor",
            "partner",
        ),
    )

    stale = bool(
        catalog_record.get(
            "stale"
        )
    )

    submission_open = (
        catalog_record.get(
            "submission_state"
        )
        == "open"
    )

    blockers = []

    if stale:
        blockers.append(
            "Catalog observation is stale; R9.0C review must wait for catalog refresh"
        )

    if not submission_open:
        blockers.append(
            "Program is not currently open for submissions"
        )

    if (
        opportunity.get(
            "offers_bounties"
        )
        is not True
    ):
        blockers.append(
            "Program is not currently marked as bounty-paying"
        )

    return {
        "schema":
            "jarvis-bounty-program-review-packet-r9.10b",

        "handle":
            raw.get("handle"),

        "name":
            raw.get("name"),

        "program_url":
            catalog_record.get(
                "program_url"
            ),

        "ranking": {
            "lane":
                opportunity.get(
                    "lane"
                ),

            "automation_viability_score":
                opportunity.get(
                    "automation_viability_score"
                ),

            "manual_hunt_viability_score":
                opportunity.get(
                    "manual_hunt_viability_score"
                ),

            "payout_score":
                opportunity.get(
                    "payout_score"
                ),
        },

        "program_state": {
            "offers_bounties":
                raw.get(
                    "offers_bounties"
                ),

            "submission_state":
                raw.get(
                    "submission_state"
                ),

            "visibility":
                raw.get(
                    "state"
                ),

            "open_scope":
                raw.get(
                    "open_scope"
                ),

            "gold_standard_safe_harbor":
                raw.get(
                    "gold_standard_safe_harbor"
                ),

            "fast_payments":
                raw.get(
                    "fast_payments"
                ),

            "triage_active":
                raw.get(
                    "triage_active"
                ),

            "catalog_stale":
                stale,
        },

        "automation_policy": {
            "classification":
                signals.get(
                    "automation_policy"
                ),

            "confidence":
                signals.get(
                    "policy_confidence"
                ),

            "evidence":
                automation_evidence,

            "human_confirmation_required":
                True,
        },

        "reward_evidence": {
            "currency":
                raw.get(
                    "currency"
                ),

            "policy_mentions":
                signals.get(
                    "payout_mentions",
                    [],
                ),

            "maximum_policy_mention":
                signals.get(
                    "payout_max_mention"
                ),

            "authoritative":
                False,

            "note":
                (
                    "Amounts are parsed from policy text "
                    "and require human confirmation."
                ),
        },

        "review_evidence": {
            "scope":
                scope_evidence,

            "accounts":
                account_evidence,

            "rate_limits":
                rate_limit_evidence,

            "third_party_boundaries":
                third_party_evidence,
        },

        "required_human_review": [
            "Refresh catalog if the stored observation is stale",
            "Review the complete current official program policy",
            "Review HackerOne structured scope",
            "Enter explicit eligible DNS or wildcard-DNS assets",
            "Enter explicit excluded DNS or wildcard-DNS assets",
            "Confirm automation policy and rate limits",
            "Confirm account and identity requirements",
            "Confirm customer and third-party boundaries",
            "Confirm reward table and asset-specific reward rules",
            "Acknowledge policy review before creating ProgramSnapshot",
            "Select capabilities/providers only in the separate authorization stage",
        ],

        "current_model_limits": [
            (
                "R9.0C ProgramSnapshot currently supports "
                "DNS and wildcard-DNS assets only"
            ),
            (
                "This packet does not convert URLs, APIs, "
                "mobile apps, repositories, or CIDRs into scope"
            ),
        ],

        "review_blockers":
            blockers,

        "ready_for_r90c_review":
            (
                submission_open
                and not stale
                and not blockers
            ),

        "source_provenance": {
            "catalog_run_id":
                catalog_record.get(
                    "run_id"
                ),

            "source_page":
                catalog_record.get(
                    "source_url"
                ),

            "source_sha256":
                catalog_record.get(
                    "source_sha256"
                ),

            "last_seen":
                catalog_record.get(
                    "last_seen"
                ),
        },

        # Critical boundaries.
        "structured_scope_reviewed":
            False,

        "testing_authorized":
            False,

        "execution_enabled":
            False,

        "automatic_execution_ready":
            False,

        "network_requests":
            0,

        "tasks_created":
            0,
    }
