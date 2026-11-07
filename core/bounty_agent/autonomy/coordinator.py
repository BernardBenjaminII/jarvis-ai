"""R9.14D.5B: non-executing mission coordination.

No reconnaissance, network requests, or submissions.
Approval verification is mandatory.
"""

from dataclasses import dataclass

from core.bounty_agent.autonomy.scheduler import MissionClaimStore


class CoordinationError(RuntimeError):
    pass


@dataclass(frozen=True)
class CoordinationResult:
    status: str
    claim_key: str
    session_id: str | None = None
    mission_id: str | None = None


def coordinate_mission(
    *,
    claim_store,
    agent,
    authorization,
    program,
    target,
    policy_digest,
    budget=2,
    approval_store=None,
    approval_id=None,
):
    if type(budget) is not int or not 1 <= budget <= 10:
        raise ValueError("Coordinator budget must be 1..10")

    if approval_store is None or not (
        isinstance(approval_id, str) and approval_id.strip()
    ):
        raise CoordinationError(
            "Durable approval store and approval ID required"
        )

    scope = agent.authorization_store.live_scope(authorization)

    if scope.program != program:
        raise CoordinationError("Program mismatch")

    # Fail closed before acquiring a scheduler claim.
    approval_fields = dict(
        authorization=authorization,
        program=program,
        target=target,
        policy_digest=policy_digest,
        budget=budget,
    )

    if approval_store.verify(
        approval_id, **approval_fields
    ) is not True:
        raise CoordinationError("Approval not verified")

    key = MissionClaimStore.key(
        authorization, program, target, policy_digest
    )

    result = claim_store.claim(
        authorization=authorization,
        program=program,
        target=target,
        policy_digest=policy_digest,
        approval_id=approval_id,
    )

    claim = result["claim"]

    if claim["claim_key"] != key:
        raise CoordinationError("Claim identity mismatch")

    if claim["state"] == "created":
        # Verify persisted ownership, not just claim metadata.
        with agent.db() as db:
            session = db.execute(
                """
                SELECT * FROM sessions
                WHERE operation_id=?
                """,
                (key,),
            ).fetchone()

        if session is None:
            raise CoordinationError(
                "Created claim has no correlated session"
            )

        with agent.live_store.db() as db:
            mission = db.execute(
                """
                SELECT * FROM missions
                WHERE operation_id=?
                """,
                (key,),
            ).fetchone()

        if (
            mission is None
            or session["mission"] != mission["id"]
            or claim["session_id"] != session["id"]
            or claim["mission_id"] != mission["id"]
            or session["authorization"] != authorization
            or mission["authorization"] != authorization
            or session["program"] != program
            or mission["program"] != program
            or session["root_target"] != target
            or mission["budget"] != budget
        ):
            raise CoordinationError(
                "Persisted mission ownership mismatch"
            )

        return CoordinationResult(
            status="already_created",
            claim_key=key,
            session_id=session["id"],
            mission_id=mission["id"],
        )

    if claim["state"] != "claimed":
        raise CoordinationError(
            "Claim state requires manual reconciliation"
        )

    # agent.create is independently idempotent.
    # It must not run recon or queue tasks here.
    session_id = agent.create(
        authorization,
        target,
        budget=budget,
        operation_id=key,
    )

    with agent.db() as db:
        session = db.execute(
            "SELECT * FROM sessions WHERE id=?",
            (session_id,),
        ).fetchone()

    with agent.live_store.db() as db:
        mission = db.execute(
            "SELECT * FROM missions WHERE operation_id=?",
            (key,),
        ).fetchone()

    if (
        session is None
        or mission is None
        or session["operation_id"] != key
        or session["mission"] != mission["id"]
        or session["authorization"] != authorization
        or mission["authorization"] != authorization
        or session["program"] != program
        or mission["program"] != program
        or session["root_target"] != target
        or mission["budget"] != budget
    ):
        raise CoordinationError(
            "New mission ownership verification failed"
        )

    claim_store.mark_created(
        key, session_id, mission["id"]
    )

    return CoordinationResult(
        status="mission_created",
        claim_key=key,
        session_id=session_id,
        mission_id=mission["id"],
    )
