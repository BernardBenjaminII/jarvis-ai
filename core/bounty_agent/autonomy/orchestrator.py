"""R9.15A.2: offline autonomous mission proposal orchestration.

No network access, approval issuance, mission creation,
reconnaissance, or automatic submission.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from core.bounty_agent.autonomy.catalog_controller import (
    plan_catalog_mission,
)


@dataclass(frozen=True)
class MissionProposal:
    status: str
    program: str | None = None
    target: str | None = None
    authorization_id: str | None = None
    policy_digest: str | None = None
    budget: int | None = None


def propose_mission(
    *,
    catalog,
    authorization_store,
    policy_digest,
    budget=2,
):
    """Select an eligible candidate without creating a mission."""

    if type(budget) is not int or not 1 <= budget <= 10:
        raise ValueError("Proposal budget must be 1..10")

    if not isinstance(policy_digest, str) or not policy_digest.strip():
        raise ValueError("Policy digest required")

    class NonExecutingAgent:
        def create(self, *args, **kwargs):
            raise AssertionError(
                "Mission creation forbidden during proposal"
            )

    selection = plan_catalog_mission(
        catalog=catalog,
        authorization_store=authorization_store,
        agent=NonExecutingAgent(),
        budget=budget,
    )

    if selection.status == "no_authorized_candidate":
        return MissionProposal(
            status="no_authorized_candidate",
        )

    if selection.status != "durable_approval_required":
        raise RuntimeError(
            f"Unexpected proposal selection state: {selection.status}"
        )

    return MissionProposal(
        status="awaiting_human_approval",
        program=selection.program,
        target=selection.target,
        authorization_id=selection.authorization_id,
        policy_digest=policy_digest,
        budget=budget,
    )


def proposal_dict(proposal: MissionProposal):
    return asdict(proposal)



def queue_mission_proposal(
    *,
    catalog,
    authorization_store,
    proposal_store,
    policy_digest,
    budget=2,
    ttl=3600,
):
    """Select and persist a proposal without issuing approval.

    This function never creates a mission, runs reconnaissance,
    or grants execution authority.
    """
    proposal = propose_mission(
        catalog=catalog,
        authorization_store=authorization_store,
        policy_digest=policy_digest,
        budget=budget,
    )

    if proposal.status != "awaiting_human_approval":
        return {
            "status": proposal.status,
            "proposal": None,
        }

    record = proposal_store.create(
        program=proposal.program,
        target=proposal.target,
        authorization_id=proposal.authorization_id,
        policy_digest=proposal.policy_digest,
        budget=proposal.budget,
        ttl=ttl,
    )

    return {
        "status": "proposal_queued",
        "proposal": record,
    }
