"""R9.20D: Mission-aware, non-executing reconnaissance advisory.

Delegates scope, tool-permission, dependency and budget checks
to the existing R9.16B planner. Synthetic targets only.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.recon_planner import (
    build_recon_plan,
)
from core.bounty_worker.identity import inventory


def build_mission_advisory(
    *,
    authorization_store,
    authorization_id: str,
    program: str,
    target: str,
    budget: int,
    tool_inventory: dict | None = None,
) -> dict:
    if (
        not isinstance(authorization_id, str)
        or not authorization_id
        or not isinstance(program, str)
        or not program
        or not isinstance(target, str)
        or not target
    ):
        raise ValueError("Invalid mission identity")

    # Use the existing planner's scope, budget and dependency
    # validation. Never broaden its target restrictions.
    plan = build_recon_plan(
        authorization_store=authorization_store,
        authorization_id=authorization_id,
        program=program,
        target=target,
        budget=budget,
        tool_inventory=(
            inventory()
            if tool_inventory is None
            else tool_inventory
        ),
    )

    if (
        plan.get("execution_started") is not False
        or plan.get("automatic_execution_allowed") is not False
        or any(
            task.get("execution_allowed") is not False
            for task in plan.get("tasks", [])
        )
    ):
        raise ValueError("Unsafe reconnaissance plan")

    return {
        "schema": "jarvis.bounty.mission_advisory.r920d",
        "mode": "offline_planning",
        "authorization_checked": True,
        "execution_authorized": False,
        "execution_started": False,
        "automatic_execution_allowed": False,
        "submission_authorized": False,
        "human_review_required": True,
        "program": plan["program"],
        "target": plan["target"],
        "authorization_id": plan["authorization_id"],
        "budget": plan["budget"],
        "planned_cost": plan["planned_cost"],
        "recommended_tasks": plan["tasks"],
        "blocked_tasks": plan["blocked"],
        "supported_environment": "synthetic_example_only",
    }
