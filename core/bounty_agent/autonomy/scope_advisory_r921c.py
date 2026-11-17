"""R9.21C — Offline scope-aware workstation advisory.

Tool availability is never equivalent to policy permission.
No network operations or execution authorization.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.program_scope_review_r921b import (
    assess_reviewed_target,
)
from core.bounty_worker.identity import inventory


ACTIVITIES = (
    ("subdomain_discovery", ("subfinder", "amass")),
    ("dns_resolution", ("dnsx",)),
    ("http_probe", ("httpx",)),
)


def build_scope_advisory(
    *,
    draft: dict,
    review: dict,
    target: str,
    tool_inventory: dict | None = None,
) -> dict:
    assessment = assess_reviewed_target(
        draft, review, target
    )

    tools = inventory() if tool_inventory is None else tool_inventory

    if not isinstance(tools, dict):
        raise ValueError("Invalid workstation inventory")

    activities = []

    for capability, names in ACTIVITIES:
        detected = []

        for name in names:
            record = tools.get(name, {})

            if not isinstance(record, dict):
                record = {}

            # httpx needs additional identity inspection because
            # a Python HTTP client can have the same command name.
            present = (
                record.get("recon_available") is True
                if name == "httpx"
                else record.get("executable_present") is True
            )

            detected.append({
                "tool": name,
                "detected": present,
                "identity_verified": False,
                "execution_allowed": False,
            })

        activities.append({
            "capability": capability,
            "tools": detected,
            "activity_permission": "not_established",
            "recommendation_state": "review_required",
            "execution_allowed": False,
            "human_review_required": True,
        })

    return {
        "schema": "jarvis.bounty.scope_advisory.r921c",
        "mode": "offline_advisory",
        "platform": draft["platform"],
        "program": draft["program"],
        "target": assessment["hostname"],
        "target_classification": assessment["classification"],
        "advisory_eligible": assessment["advisory_eligible"],
        "policy_sha256": assessment["policy_sha256"],
        "activities": activities,
        "policy_permissions_verified": False,
        "testing_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "human_review_required": True,
    }
