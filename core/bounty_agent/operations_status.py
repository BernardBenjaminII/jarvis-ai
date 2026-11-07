"""R9.13B.3 — Read-only Bounty Agent operations status."""

import time

from core.bounty_authorization import AuthorizationDenied


TASK_STATES = (
    "queued",
    "running",
    "completed",
    "failed",
    "interrupted",
)


def build_operations_status(agent, session_id):
    """Summarize one existing session without executing tools."""

    report = agent.report(session_id)
    session = report["session"]
    mission = report["mission"]["mission"]
    tasks = report["mission"].get("tasks", [])
    options = report.get("options", [])

    authorization_id = session["authorization"]

    # Never expose scope documents or authorization secrets.
    authorization = {
        "status": "unavailable",
        "expires_at": None,
    }

    try:
        record = agent.authorization_store.get(
            authorization_id
        )

        authorization["expires_at"] = record["expires"]

        if record["revoked"]:
            authorization["status"] = "revoked"

        elif time.time() >= record["expires"]:
            authorization["status"] = "expired"

        else:
            try:
                agent.authorization_store.live_scope(
                    authorization_id
                )
                authorization["status"] = "valid"
            except AuthorizationDenied:
                authorization["status"] = "invalid"

    except AuthorizationDenied:
        pass

    counts = {
        state: sum(
            task.get("state") == state
            for task in tasks
        )
        for state in TASK_STATES
    }

    candidates = agent.live_store.interrupted_candidates(
        older_than=300
    )

    recovery = [
        {
            "task_id": candidate["id"],
            "status": "requires_operator_review",
        }
        for candidate in candidates
        if candidate["mission"] == session["mission"]
    ]

    return {
        "schema": "jarvis.bounty.operations.r913b3",
        "session_id": session["id"],
        "mission_id": session["mission"],
        "session_state": session["state"],
        "authorization": authorization,
        "tasks": counts,
        "target_budget": mission["budget"],
        "execution_units_used": mission["used"],
        "awaiting_human": sum(
            option.get("state") == "awaiting_human"
            for option in options
        ),
        "recovery": {
            "interrupted_count": counts["interrupted"],
            "potentially_abandoned": recovery,
            "automatic_retry_allowed": False,
        },
    }
