"""R9.22C2B: bind advisory capability analysis to stored reviews.

An operator attestation is not independent policy verification.
No authorization, mission creation, or security-tool execution.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.program_policy_capability_r922c2 import (
    assess_program_capabilities,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    assess_reviewed_target,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)


def assess_persistent_review(
    *,
    draft_id,
    draft,
    inventory,
    review_store=None,
    review_id=None,
    restriction_evidence=None,
):
    """Return an offline advisory bound to the exact draft identity."""

    if not isinstance(draft_id, str) or not draft_id.strip():
        raise OpportunityQueueError("Draft identifier required")

    capability = assess_program_capabilities(
        draft,
        inventory,
        restriction_evidence=restriction_evidence,
    )

    attestation = {
        "state": "not_attested",
        "review_id": None,
        "stored_operator_attestation_valid": False,
        "policy_digest_matched": False,
        "reviewed_at": None,
        "expires_at": None,
        "independently_verified": False,
        "category_classifications_persisted": False,
    }

    if review_id is not None:
        if not isinstance(review_id, str) or not review_id.strip():
            raise OpportunityQueueError("Invalid review identifier")

        if review_store is None:
            raise OpportunityQueueError("Review store required")

        try:
            record = review_store.get(
                review_id,
                draft_id=draft_id,
                draft=draft,
            )

            if (
                not isinstance(record, dict)
                or record.get("id") != review_id
                or record.get("draft_id") != draft_id
                or record.get("execution_authorized") is not False
                or record.get("submission_authorized") is not False
            ):
                raise ValueError("Unsafe stored review")

            review = record["review"]

            assessment = assess_reviewed_target(
                draft,
                review,
                draft["in_scope"][0],
            )

            if (
                assessment.get("advisory_eligible") is not True
                or assessment.get("execution_authorized") is not False
                or assessment.get("testing_authorized") is not False
                or assessment.get("policy_sha256")
                != capability["policy_sha256"]
            ):
                raise ValueError("Invalid review binding")

        except (ValueError, KeyError, TypeError, IndexError):
            attestation["state"] = "invalid_or_expired"

        else:
            attestation.update({
                "state": "operator_attested_current",
                "review_id": review_id,
                "stored_operator_attestation_valid": True,
                "policy_digest_matched": True,
                "reviewed_at": review["reviewed_at"],
                "expires_at": review["expires_at"],
            })

    return {
        "schema": "jarvis.bounty.program_review_evidence.r922c2b",
        "mode": "offline_advisory",
        "draft_id": draft_id,
        "policy_sha256": capability["policy_sha256"],
        "attestation": attestation,
        "capability_assessment": capability,
        "human_review_required": True,
        "independent_policy_verification": False,
        "program_specific_fit_verified": False,
        "network_requests": 0,
        "testing_authorized": False,
        "execution_enabled": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
    }
