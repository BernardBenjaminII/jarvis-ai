"""R9.14D.2: read-only recovery inspection.

No mission creation, claim release, network access,
or automatic record adoption.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryFinding:
    claim_key: str
    status: str
    session_ids: tuple[str, ...] = ()
    mission_ids: tuple[str, ...] = ()
    reason: str = ""


def inspect_pending_claims(claim_store, agent):
    """Correlate pending claims with persisted sessions.

    Matches are diagnostic, not proof of claim ownership.
    """
    findings = []

    with agent.db() as db:
        sessions = [
            dict(row)
            for row in db.execute(
                """
                SELECT id, authorization, mission,
                       program, root_target, created
                FROM sessions
                """
            )
        ]

    for claim in claim_store.pending():
        matches = [
            session
            for session in sessions
            if (
                session["authorization"]
                == claim["authorization"]
                and session["program"]
                == claim["program"]
                and session["root_target"]
                == claim["target"]
            )
        ]

        # A session created before the claim cannot
        # establish ownership of that claim.
        matches = [
            session
            for session in matches
            if session["created"] >= claim["created"]
        ]

        if not matches:
            finding = RecoveryFinding(
                claim_key=claim["claim_key"],
                status="unresolved",
                reason=(
                    "No post-claim agent session found; "
                    "mission store requires separate inspection"
                ),
            )

        elif len(matches) == 1:
            finding = RecoveryFinding(
                claim_key=claim["claim_key"],
                status="candidate_match",
                session_ids=(matches[0]["id"],),
                mission_ids=(matches[0]["mission"],),
                reason=(
                    "One matching session; ownership and "
                    "live mission integrity not yet verified"
                ),
            )

        else:
            finding = RecoveryFinding(
                claim_key=claim["claim_key"],
                status="ambiguous",
                session_ids=tuple(
                    item["id"] for item in matches
                ),
                mission_ids=tuple(
                    item["mission"] for item in matches
                ),
                reason=(
                    "Multiple matching sessions; "
                    "manual reconciliation required"
                ),
            )

        findings.append(finding)

    return findings


@dataclass(frozen=True)
class MissionIntegrityFinding:
    mission_id: str
    status: str
    session_ids: tuple[str, ...] = ()
    authorization: str = ""
    program: str = ""
    reason: str = ""


def inspect_mission_integrity(agent, live_store):
    """Inspect persisted session/mission relationships.

    Read-only. Does not attribute orphaned missions to claims,
    alter mission state, or execute any tasks.
    """
    with agent.db() as db:
        sessions = [
            dict(row)
            for row in db.execute(
                """
                SELECT id, mission, authorization, program
                FROM sessions
                ORDER BY id
                """
            )
        ]

    with live_store.db() as db:
        missions = [
            dict(row)
            for row in db.execute(
                """
                SELECT id, authorization, program, state
                FROM missions
                ORDER BY id
                """
            )
        ]

    by_mission = {}
    for session in sessions:
        by_mission.setdefault(
            session["mission"], []
        ).append(session)

    mission_ids = {item["id"] for item in missions}
    findings = []

    for mission in missions:
        matches = by_mission.get(mission["id"], [])
        ids = tuple(item["id"] for item in matches)

        if not matches:
            status = "orphaned"
            reason = "No agent session references this mission"

        elif len(matches) > 1:
            status = "ambiguous"
            reason = "Multiple agent sessions reference one mission"

        elif (
            matches[0]["authorization"] != mission["authorization"]
            or matches[0]["program"] != mission["program"]
        ):
            status = "integrity_mismatch"
            reason = "Session and mission ownership disagree"

        else:
            status = "linked"
            reason = "One matching session with consistent ownership"

        findings.append(
            MissionIntegrityFinding(
                mission_id=mission["id"],
                status=status,
                session_ids=ids,
                authorization=mission["authorization"],
                program=mission["program"],
                reason=reason,
            )
        )

    for session in sessions:
        if session["mission"] not in mission_ids:
            findings.append(
                MissionIntegrityFinding(
                    mission_id=session["mission"],
                    status="missing_mission",
                    session_ids=(session["id"],),
                    authorization=session["authorization"],
                    program=session["program"],
                    reason="Session references a nonexistent mission",
                )
            )

    return findings
