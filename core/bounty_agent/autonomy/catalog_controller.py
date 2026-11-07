"""R9.14C: catalog-driven, authorization-gated mission planning.

No reconnaissance, network access, or automatic submission.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from core.bounty_catalog.opportunity import rank_catalog
from core.bounty_agent.autonomy.coordinator import (
    coordinate_mission,
)
from core.bounty_agent.autonomy.authorization_bridge import (
    Candidate,
    AuthorizationBinding,
    select_authorized_candidate,
)


@dataclass(frozen=True)
class MissionSelection:
    status: str
    program: str | None = None
    target: str | None = None
    authorization_id: str | None = None
    session_id: str | None = None
    mission_id: str | None = None


def existing_authorizations(store):
    """Read existing records; never manufacture approvals."""
    with store.db() as db:
        rows = db.execute(
            """
            SELECT id, program, scope_json
            FROM authorizations
            WHERE revoked=0 AND expires>?
            ORDER BY reviewed_at DESC
            """,
            (time.time(),),
        ).fetchall()

    return [dict(row) for row in rows]


def plan_catalog_mission(
    *,
    catalog,
    authorization_store,
    agent,
    autonomous_approval_ids=(),
    budget=2,
    claim_store=None,
    approval_store=None,
    approval_id=None,
    policy_digest=None,
):
    """Select and create one mission without starting recon."""
    if type(budget) is not int or not 1 <= budget <= 10:
        raise ValueError("Autonomous planning budget must be 1..10")

    ranked = rank_catalog(catalog)
    opportunities = ranked.get("opportunities", [])
    records = existing_authorizations(authorization_store)

    # Candidate discovery is not permission to create a mission.
    # All active authorizations may contribute candidates.
    approved_ids = {record["id"] for record in records}
    candidates = []
    bindings = []

    for opportunity in opportunities:
        handle = opportunity.get("handle")

        if not isinstance(handle, str) or not handle:
            continue

        # Skip closed or otherwise blocked programs.
        if opportunity.get("blockers"):
            continue

        if opportunity.get("lane") == "SKIP":
            continue

        # A ranking score never grants execution permission.
        # Require explicit, reviewable policy evidence.
        if opportunity.get("submission_state") != "open":
            continue

        signals = opportunity.get("policy_signals") or {}
        policy = signals.get("automation_policy")

        if policy not in {
            "explicitly_permitted",
            "conditionally_permitted",
        }:
            continue

        score = max(
            opportunity.get("automation_viability_score") or 0,
            opportunity.get("manual_hunt_viability_score") or 0,
        )

        for record in records:
            if record["program"] != handle:
                continue

            if record["id"] not in approved_ids:
                continue

            try:
                scope = authorization_store.live_scope(record["id"])
            except (ValueError, KeyError):
                continue

            # For the first integration, only explicitly listed
            # hostnames are considered; never invent targets.
            for target in scope.include:
                if target.startswith("*."):
                    continue

                candidates.append(
                    Candidate(handle, target, float(score))
                )
                bindings.append(
                    AuthorizationBinding(
                        authorization_id=record["id"],
                        program=handle,
                        target=target,
                        reviewed=True,
                        active=True,
                    )
                )

    selected = select_authorized_candidate(
        candidates,
        bindings,
        scope_store=authorization_store,
    )

    if selected["status"] != "authorized_candidate_selected":
        return MissionSelection(status="no_authorized_candidate")

    # Candidate selection alone cannot authorize mission creation.
    if autonomous_approval_ids or not (
        claim_store is not None
        and approval_store is not None
        and isinstance(approval_id, str)
        and approval_id.strip()
        and isinstance(policy_digest, str)
        and policy_digest.strip()
    ):
        return MissionSelection(
            status="durable_approval_required",
            program=selected["program"],
            target=selected["target"],
            authorization_id=selected["authorization_id"],
        )

    coordinated = coordinate_mission(
        claim_store=claim_store,
        agent=agent,
        authorization=selected["authorization_id"],
        program=selected["program"],
        target=selected["target"],
        policy_digest=policy_digest,
        budget=budget,
        approval_store=approval_store,
        approval_id=approval_id,
    )

    session_id = coordinated.session_id
    mission_id = coordinated.mission_id

    return MissionSelection(
        status=coordinated.status,
        program=selected["program"],
        target=selected["target"],
        authorization_id=selected["authorization_id"],
        session_id=session_id,
        mission_id=mission_id,
    )
