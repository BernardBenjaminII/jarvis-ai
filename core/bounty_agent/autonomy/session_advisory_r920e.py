"""R9.20E: Read-only advisory for an existing bounty session."""

from __future__ import annotations

from core.bounty_agent.autonomy.mission_advisory_r920d import (
    build_mission_advisory,
)


class SessionAdvisoryError(ValueError):
    pass


def build_session_advisory(agent, session_id: str) -> dict:
    if not isinstance(session_id, str) or not session_id:
        raise SessionAdvisoryError("Invalid session identifier")

    try:
        report = agent.report(session_id)
    except (KeyError, ValueError) as exc:
        raise SessionAdvisoryError(
            "Session unavailable"
        ) from exc

    try:
        session = report["session"]
        mission = report["mission"]["mission"]

        if session["id"] != session_id:
            raise SessionAdvisoryError("Session identity mismatch")

        if session["mission"] != mission["id"]:
            raise SessionAdvisoryError("Mission identity mismatch")

        authorization_id = session["authorization"]
        program = session["program"]
        target = session["root_target"]
        original_budget = mission["budget"]

        if type(original_budget) is not int or original_budget < 1:
            raise SessionAdvisoryError("Invalid mission budget")

    except (KeyError, TypeError) as exc:
        raise SessionAdvisoryError(
            "Invalid session report"
        ) from exc

    # R9.16B supports a maximum of 10 planning units.
    # This cap cannot authorize execution.
    planning_budget = min(original_budget, 10)

    plan = build_mission_advisory(
        authorization_store=agent.authorization_store,
        authorization_id=authorization_id,
        program=program,
        target=target,
        budget=planning_budget,
    )

    return {
        **plan,
        "schema": "jarvis.bounty.session_advisory.r920e",
        "session_id": session_id,
        "mission_id": session["mission"],
        "original_mission_budget": original_budget,
        "planning_budget_capped": original_budget > 10,
        "execution_authorized": False,
        "execution_started": False,
        "automatic_execution_allowed": False,
        "submission_authorized": False,
        "human_review_required": True,
    }
