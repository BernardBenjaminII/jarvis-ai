"""R9.22C2A: offline, restriction-aware capability assessment.

Operator-classified restrictions are advisory, not verified permissions.
No network traffic, mission creation, or tool execution.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.program_scope_review_r921b import (
    validate_draft,
)
from core.bounty_agent.autonomy.program_capability_fit_r922c1 import (
    TOOL_GROUPS,
    _workstation_readiness,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)


def assess_program_capabilities(
    draft,
    inventory,
    *,
    restriction_evidence=None,
):
    """Flag tool categories using explicitly supplied restriction evidence."""

    digest = validate_draft(draft)
    workstation = _workstation_readiness(inventory)

    if any((
        draft.get("review_status") != "unverified",
        draft.get("scope_verified") is not False,
        draft.get("execution_authorized") is not False,
        draft.get("submission_authorized") is not False,
    )):
        raise OpportunityQueueError("Unsafe imported policy state")

    if restriction_evidence is None:
        restriction_evidence = {}

    if not isinstance(restriction_evidence, dict):
        raise OpportunityQueueError("Invalid restriction classification")

    recorded = set(draft["restrictions"])
    classified = {}

    for category, evidence in restriction_evidence.items():
        if category not in TOOL_GROUPS:
            raise OpportunityQueueError("Unknown tool category")

        if not isinstance(evidence, str) or evidence not in recorded:
            raise OpportunityQueueError(
                "Restriction evidence must match imported policy text"
            )

        classified[category] = evidence

    assessments = {}

    for category in TOOL_GROUPS:
        availability = workstation["categories"][category]
        flagged = category in classified

        assessments[category] = {
            "tools": list(TOOL_GROUPS[category]),
            "availability": availability["status"],
            "available_tools": availability["available_tools"],
            "missing_tools": availability["missing_tools"],
            "policy_status": (
                "operator_flagged_restriction_unverified"
                if flagged else "permission_unknown"
            ),
            "restriction_evidence": classified.get(category),
            "program_specific_fit": None,
            "execution_allowed": False,
        }

    return {
        "schema": "jarvis.bounty.program_policy_capability.r922c2a",
        "mode": "offline_advisory",
        "program": draft["program"],
        "platform": draft["platform"],
        "policy_sha256": digest,
        "listed_host_count": len(draft["in_scope"]),
        "excluded_host_count": len(draft["out_of_scope"]),
        "review_status": "unverified",
        "independent_policy_verification": False,
        "human_review_required": True,
        "network_requests": 0,
        "testing_authorized": False,
        "execution_enabled": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
        "categories": assessments,
    }
