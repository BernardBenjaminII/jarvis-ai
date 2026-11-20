"""R9.22C1: read-only capability-aware opportunity review ranking.

Combines existing program rankings with general Kali tool availability.
Does not infer program-specific tool permission or create missions.
"""

from __future__ import annotations

from core.capabilities.kali_workstation import TOOLS
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)


TOOL_GROUPS = {
    "subdomain_discovery": ("subfinder", "amass"),
    "dns_resolution": ("dnsx",),
    "http_observation": ("httpx",),
    "content_discovery": ("ffuf",),
    "template_analysis": ("nuclei",),
    "network_inventory": ("nmap", "masscan"),
}

LANE_PRIORITY = {
    "POLICY_REVIEW": 0,
    "MANUAL_A": 1,
    "MANUAL_B": 2,
    "IMPORTED_POLICY": 3,
    "SKIP": 4,
}


def _workstation_readiness(inventory):
    if not isinstance(inventory, dict):
        raise OpportunityQueueError("Invalid inventory")

    if (
        inventory.get("mode") != "inventory_only"
        or inventory.get("execution_authorized") is not False
    ):
        raise OpportunityQueueError("Unsafe workstation inventory")

    tools = inventory.get("tools")

    if not isinstance(tools, dict) or set(tools) != set(TOOLS):
        raise OpportunityQueueError("Unexpected workstation tools")

    installed = []

    for name in TOOLS:
        entry = tools[name]

        if (
            not isinstance(entry, dict)
            or type(entry.get("installed")) is not bool
        ):
            raise OpportunityQueueError("Invalid tool installation state")

        if entry["installed"]:
            installed.append(name)

    if (
        type(inventory.get("tool_count")) is not int
        or inventory["tool_count"] != len(TOOLS)
        or type(inventory.get("installed_count")) is not int
        or inventory["installed_count"] != len(installed)
    ):
        raise OpportunityQueueError("Inconsistent inventory counts")

    expected_state = (
        "ready" if len(installed) == len(TOOLS) else "degraded"
    )

    if inventory.get("state") != expected_state:
        raise OpportunityQueueError("Inconsistent inventory state")

    installed_set = set(installed)
    categories = {}

    for category, members in TOOL_GROUPS.items():
        available = [t for t in members if t in installed_set]
        missing = [t for t in members if t not in installed_set]

        categories[category] = {
            "status": (
                "available" if not missing
                else "unavailable" if not available
                else "partial"
            ),
            "available_tools": available,
            "missing_tools": missing,
        }

    return {
        "mode": "general_tool_availability",
        "installed_tools": installed,
        "missing_tools": [
            name for name in TOOLS if name not in installed_set
        ],
        "coverage_percent": round(
            100 * len(installed) / len(TOOLS)
        ),
        "categories": categories,
        "execution_authorized": False,
    }


def rank_opportunity_reviews(queue, inventory):
    """Rank review attention without assessing target authorization."""

    if (
        not isinstance(queue, dict)
        or queue.get("schema")
        != "jarvis.bounty.program_opportunities.r922b2"
        or queue.get("mode") != "offline_unified_opportunity_queue"
        or queue.get("network_requests") != 0
        or queue.get("testing_authorized") is not False
        or queue.get("automatic_execution_allowed") is not False
        or queue.get("submission_authorized") is not False
    ):
        raise OpportunityQueueError("Unsafe opportunity queue")

    records = queue.get("opportunities")

    if (
        not isinstance(records, list)
        or len(records) > 5000
        or type(queue.get("opportunity_count")) is not int
        or queue["opportunity_count"] != len(records)
    ):
        raise OpportunityQueueError("Invalid queue records")

    workstation = _workstation_readiness(inventory)
    source_info = queue.get("sources")

    if not isinstance(source_info, dict):
        raise OpportunityQueueError("Missing source provenance")

    hackerone = source_info.get("hackerone_catalog")

    if not isinstance(hackerone, dict):
        raise OpportunityQueueError("Missing catalog provenance")

    ranked = []
    identities = set()

    for item in records:
        if not isinstance(item, dict):
            raise OpportunityQueueError("Invalid opportunity")

        if (
            item.get("testing_authorized") is not False
            or item.get("execution_enabled") is not False
            or item.get("automatic_execution_ready") is not False
            or item.get("submission_authorized") is not False
            or item.get("program_eligibility") != "unknown"
            or item.get("policy_review_status") != "unverified"
        ):
            raise OpportunityQueueError("Unsafe opportunity state")

        source = item.get("source")
        program = item.get("program")
        platform = item.get("platform")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (source, program, platform)
        ):
            raise OpportunityQueueError("Invalid opportunity identity")

        if source == "hackerone_api_snapshot":
            if hackerone.get("status") != "fresh":
                raise OpportunityQueueError(
                    "Untrusted catalog freshness"
                )

            identifier = item.get("handle")
            lane = item.get("source_lane")
            manual_score = item.get("manual_hunt_viability_score")

            if (
                platform != "hackerone"
                or not isinstance(identifier, str)
                or not identifier
                or lane not in {
                    "POLICY_REVIEW", "MANUAL_A",
                    "MANUAL_B", "SKIP"
                }
                or type(manual_score) is not int
                or not 0 <= manual_score <= 100
                or item.get("payout_values_authoritative") is not False
            ):
                raise OpportunityQueueError(
                    "Invalid HackerOne ranking"
                )

        elif source == "manual_policy_import":
            identifier = item.get("draft_id")
            lane = "IMPORTED_POLICY"
            manual_score = None

            if (
                not isinstance(identifier, str)
                or not identifier.strip()
            ):
                raise OpportunityQueueError(
                    "Invalid imported draft identity"
                )

        else:
            raise OpportunityQueueError(
                "Unsupported opportunity source"
            )

        identity = (source, identifier.casefold())

        if identity in identities:
            raise OpportunityQueueError(
                "Duplicate opportunity identity"
            )

        identities.add(identity)

        ranked.append({
            "source": source,
            "platform": platform,
            "program": program,
            "source_identifier": identifier,
            "policy_url": item.get("policy_url"),
            "review_lane": lane,
            "existing_manual_viability_score": manual_score,
            "program_specific_capability_fit": None,
            "capability_fit_status": (
                "unknown_pending_program_requirements"
            ),
            "next_action": (
                "recheck_program_status"
                if lane == "SKIP"
                else "human_policy_and_scope_review"
            ),
            "human_review_required": True,
            "testing_authorized": False,
            "execution_enabled": False,
            "automatic_execution_ready": False,
            "submission_authorized": False,
        })

    ranked.sort(
        key=lambda item: (
            LANE_PRIORITY[item["review_lane"]],
            -(
                item["existing_manual_viability_score"]
                if item["existing_manual_viability_score"] is not None
                else -1
            ),
            item["program"].casefold(),
            item["source"],
            item["source_identifier"],
        )
    )

    for position, item in enumerate(ranked, 1):
        item["review_position"] = position

    return {
        "schema": "jarvis.bounty.program_capability_fit.r922c1",
        "mode": "offline_read_only_review_ranking",
        "opportunity_count": len(ranked),
        "workstation": workstation,
        "network_requests": 0,
        "testing_authorized": False,
        "automatic_execution_allowed": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
        "opportunities": ranked,
    }
