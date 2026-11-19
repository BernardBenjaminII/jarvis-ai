"""R9.22B: offline normalization of imported bounty programs.

Program discovery and policy imports are not authorization.
No network, mission creation, or tool execution.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.program_scope_review_r921b import (
    validate_draft,
)


class OpportunityQueueError(ValueError):
    pass


def build_imported_opportunity_queue(records):
    """Build a deterministic queue from R9.21D stored draft records."""

    if not isinstance(records, list) or len(records) > 200:
        raise OpportunityQueueError("Invalid opportunity records")

    opportunities = {}
    identifiers = {}

    for record in records:
        if not isinstance(record, dict):
            raise OpportunityQueueError("Invalid record")

        draft_id = record.get("id")
        draft = record.get("draft")

        if not isinstance(draft_id, str) or not draft_id.strip():
            raise OpportunityQueueError("Draft ID required")

        if not isinstance(draft, dict):
            raise OpportunityQueueError("Draft required")

        if (
            record.get("review_status") != "unverified"
            or record.get("execution_authorized") is not False
            or record.get("submission_authorized") is not False
        ):
            raise OpportunityQueueError("Unsafe draft state")

        # Reuse the existing canonical policy validation.
        digest = validate_draft(draft)

        if draft_id in identifiers and identifiers[draft_id] != digest:
            raise OpportunityQueueError("Conflicting draft identity")

        identifiers[draft_id] = digest

        key = (draft["platform"], digest)

        if key in opportunities:
            continue

        opportunities[key] = {
            "draft_id": draft_id,
            "platform": draft["platform"],
            "program": draft["program"],
            "policy_url": draft["policy_url"],
            "policy_sha256": digest,
            "listed_asset_count": len(draft["in_scope"]),
            "source": "manual_policy_import",
            "policy_review_status": "unverified",
            "program_eligibility": "unknown",
            "reward_status": "unverified",
            "recommendation": "human_policy_review_required",
            "testing_authorized": False,
            "execution_enabled": False,
            "automatic_execution_ready": False,
            "submission_authorized": False,
        }

    ordered = sorted(
        opportunities.values(),
        key=lambda item: (
            item["platform"],
            item["program"].casefold(),
            item["policy_sha256"],
        ),
    )

    return {
        "schema": "jarvis.bounty.program_opportunities.r922b1",
        "mode": "offline_imported_policy_queue",
        "opportunity_count": len(ordered),
        "network_requests": 0,
        "testing_authorized": False,
        "automatic_execution_allowed": False,
        "opportunities": ordered,
    }
