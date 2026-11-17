"""R9.20A: Advisory-only Kali workstation capability matching.

No network requests, scanner execution, authorization, or
modification of R9.18's fixed localhost experiment catalog.
"""

from __future__ import annotations

from core.capabilities.kali_workstation import inventory_snapshot
from core.bounty_agent.autonomy.hypothesis_ranker_r918d1 import (
    CAPABILITIES as LAB_EXPERIMENTS,
)


# Tool preferences for future supervised workflows.
# These are NOT execution permissions.
ACTIVITIES = {
    "subdomain_discovery": ("subfinder", "amass"),
    "dns_resolution": ("dnsx",),
    "http_probing": ("httpx",),
    "port_discovery": ("nmap", "masscan"),
    "content_discovery": ("ffuf",),
    "template_analysis": ("nuclei",),
}


def workstation_advisory(
    inventory: dict | None = None,
) -> dict:
    """Match installed tools to activities without executing them."""

    if inventory is None:
        inventory = inventory_snapshot()

    if not isinstance(inventory, dict):
        raise ValueError("Invalid workstation inventory")

    tools = inventory.get("tools")

    if not isinstance(tools, dict):
        raise ValueError("Missing workstation tools")

    activities = {}

    for activity, candidates in ACTIVITIES.items():
        available = []

        for name in candidates:
            entry = tools.get(name)

            if (
                isinstance(entry, dict)
                and entry.get("installed") is True
                and isinstance(entry.get("path"), str)
                and entry["path"].startswith("/")
            ):
                available.append({
                    "tool": name,
                    "path": entry["path"],
                    "installed": True,
                })

        activities[activity] = {
            "state": (
                "available_for_review"
                if available else "unavailable"
            ),
            "tools": available,
            "execution_allowed": False,
            "human_review_required": True,
        }

    return {
        "version": "r920a",
        "mode": "advisory_only",
        "execution_authorized": False,
        "submission_authorized": False,
        "activities": activities,
        "legacy_lab_experiments": {
            name: {
                "environment": "fixed_local_lab",
                "mapped_to_kali_tool": False,
                "execution_allowed": False,
            }
            for name in sorted(LAB_EXPERIMENTS)
        },
        "arsenal_state": (
            inventory.get("arsenal", {}).get("state", "unknown")
            if isinstance(inventory.get("arsenal"), dict)
            else "unknown"
        ),
    }
