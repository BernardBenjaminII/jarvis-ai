"""R9.21E: read-only policy review to authorization matching.

A policy review is NOT execution authorization.
This module never creates authorizations or starts missions.
"""

from __future__ import annotations

from core.bounty_agent.autonomy.program_scope_review_r921b import (
    assess_reviewed_target,
)


def assess_authorization_binding(
    *,
    draft,
    review,
    hostname,
    authorization_id,
    authorization_store,
):
    """Match a reviewed exact hostname to an existing live authorization."""

    result = {
        "schema": "jarvis.bounty.scope_binding.r921e",
        "status": "not_authorized",
        "policy_review_valid": False,
        "authorization_match": False,
        "proposal_ready": False,
        "execution_started": False,
        "submission_authorized": False,
    }

    if not isinstance(hostname, str):
        return {**result, "reason": "invalid_target"}

    if (
        not hostname
        or hostname != hostname.strip().lower()
        or "*" in hostname
    ):
        return {**result, "reason": "invalid_target"}

    try:
        assessment = assess_reviewed_target(
            draft, review, hostname
        )
    except (ValueError, KeyError, TypeError):
        return {**result, "reason": "invalid_or_expired_policy_review"}

    if not (
        assessment.get("advisory_eligible") is True
        and assessment.get("classification")
        == "listed_in_unverified_draft"
        and assessment.get("execution_authorized") is False
    ):
        return {**result, "reason": "target_not_reviewed_in_scope"}

    result["policy_review_valid"] = True

    if not isinstance(authorization_id, str) or not authorization_id.strip():
        return {**result, "reason": "separate_authorization_required"}

    if authorization_store is None:
        return {**result, "reason": "authorization_store_unavailable"}

    try:
        scope = authorization_store.live_scope(
            authorization_id
        )

        if scope.program != draft["program"]:
            return {**result, "reason": "authorization_program_mismatch"}

        if not scope.permits_host(hostname):
            return {**result, "reason": "authorization_excludes_target"}

    except (ValueError, KeyError, TypeError, AttributeError):
        return {**result, "reason": "authorization_inactive_or_invalid"}

    return {
        **result,
        "status": "existing_authorization_matched",
        "authorization_match": True,
        "reason": "separate_live_authorization_confirmed",
        # Deliberately never grant proposal/execution permission here.
        "proposal_ready": False,
        "execution_started": False,
    }
