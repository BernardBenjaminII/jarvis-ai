
"""R9.16B: non-executing, authorization-aware recon planner."""

from __future__ import annotations

from core.bounty_worker.identity import inventory


CAPABILITIES = (
    ("subdomain_discovery", "subfinder", ()),
    ("dns_resolution", "dnsx", ("subdomain_discovery",)),
    ("http_probe", "httpx", ("dns_resolution",)),
)

# The planner does not invoke any of these binaries.
# Dependencies are advisory planning dependencies.


class ReconPlanningError(ValueError):
    pass


def build_recon_plan(
    *,
    authorization_store,
    authorization_id,
    program,
    target,
    budget,
    tool_inventory=None,
):
    if type(budget) is not int or not 1 <= budget <= 10:
        raise ReconPlanningError("Invalid mission budget")

    if not isinstance(target, str) or not target.endswith(
        ".example"
    ):
        raise ReconPlanningError(
            "R9.16B permits synthetic .example targets only"
        )

    scope = authorization_store.live_scope(authorization_id)

    if scope.program != program or not scope.permits_host(target):
        raise ReconPlanningError("Target outside authorization")

    tools = inventory() if tool_inventory is None else tool_inventory

    if not isinstance(tools, dict):
        raise ReconPlanningError("Invalid capability inventory")

    allowed = set(scope.logical_capabilities)
    selected = []
    blocked = []

    for capability, tool, dependencies in CAPABILITIES:
        reason = None

        if capability not in allowed:
            reason = "capability_not_authorized"
        else:
            try:
                scope.require(target, tool)
            except (ValueError, KeyError):
                reason = "tool_not_authorized"

        if reason is None:
            # This is a presence check, not an operational
            # readiness or binary trust assertion.
            record = tools.get(tool, {})
            if not isinstance(record, dict):
                reason = "invalid_tool_inventory"
            elif tool == "httpx":
                if not record.get("recon_available", False):
                    reason = "tool_identity_unverified"
            elif not record.get("executable_present", False):
                reason = "tool_not_installed"

        if reason is None:
            selected_capabilities = {
                item["capability"] for item in selected
            }
            if not all(
                dependency in selected_capabilities
                for dependency in dependencies
            ):
                reason = "dependency_unavailable"

        if reason is None and len(selected) >= budget:
            reason = "budget_exhausted"

        if reason:
            blocked.append({
                "capability": capability,
                "tool": tool,
                "reason": reason,
            })
            continue

        selected.append({
            "order": len(selected) + 1,
            "capability": capability,
            "tool": tool,
            "target": target,
            "cost": 1,
            "dependencies": [
                dependency
                for dependency in dependencies
                if any(
                    item["capability"] == dependency
                    for item in selected
                )
            ],
            "execution_allowed": False,
            "reason": "Authorized capability with detected tool",
        })

    return {
        "schema": "jarvis.bounty.recon_plan.r916b",
        "program": program,
        "target": target,
        "authorization_id": authorization_id,
        "mode": "offline_planning",
        "execution_started": False,
        "automatic_execution_allowed": False,
        "budget": budget,
        "planned_cost": len(selected),
        "tasks": selected,
        "blocked": blocked,
    }
