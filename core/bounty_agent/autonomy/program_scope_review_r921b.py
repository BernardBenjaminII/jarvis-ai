"""R9.21B: operator-attested, advisory-only scope review."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.bounty_agent.autonomy.program_scope_r921a import (
    SCHEMA,
    ScopeIntakeError,
    assess_scope_target,
    create_scope_draft,
)


class ScopeReviewError(ValueError):
    pass


def utc_time(value):
    if not isinstance(value, str):
        raise ScopeReviewError("Timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ScopeReviewError("Invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ScopeReviewError("Timezone required")
    return parsed.astimezone(timezone.utc)


def validate_draft(draft):
    if not isinstance(draft, dict) or draft.get("schema") != SCHEMA:
        raise ScopeReviewError("Unknown draft schema")

    if (
        draft.get("review_status") != "unverified"
        or draft.get("scope_verified") is not False
        or draft.get("execution_authorized") is not False
        or draft.get("submission_authorized") is not False
    ):
        raise ScopeReviewError("Draft safety state invalid")

    try:
        rebuilt = create_scope_draft(
            platform=draft["platform"],
            program=draft["program"],
            policy_url=draft["policy_url"],
            in_scope=draft["in_scope"],
            out_of_scope=draft["out_of_scope"],
            restrictions=draft["restrictions"],
        )
    except (KeyError, TypeError, ValueError, ScopeIntakeError) as exc:
        raise ScopeReviewError("Invalid scope draft") from exc

    if rebuilt["policy_sha256"] != draft.get("policy_sha256"):
        raise ScopeReviewError("Scope digest mismatch")

    # Reject noncanonical data, including reordered lists.
    for field in (
        "platform", "program", "policy_url",
        "in_scope", "out_of_scope", "restrictions",
    ):
        if rebuilt[field] != draft[field]:
            raise ScopeReviewError("Noncanonical scope draft")

    return rebuilt["policy_sha256"]


def review_scope_draft(
    draft,
    *,
    reviewer,
    source_checked_at,
    source_matches,
):
    digest = validate_draft(draft)

    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ScopeReviewError("Reviewer identity required")

    if source_matches is not True:
        raise ScopeReviewError(
            "Operator must confirm source matches imported policy"
        )

    checked = utc_time(source_checked_at)
    now = datetime.now(timezone.utc)

    if checked > now + timedelta(minutes=5):
        raise ScopeReviewError("Future source review timestamp")

    if now - checked > timedelta(days=1):
        raise ScopeReviewError("Source review is not recent")

    return {
        "schema": "jarvis.bounty.scope_review.r921b",
        "platform": draft["platform"],
        "program": draft["program"],
        "policy_sha256": digest,
        "reviewer": reviewer.strip(),
        "reviewed_at": now.isoformat(),
        "source_checked_at": checked.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "review_status": "operator_attested",
        "verification_method": "manual_source_comparison",
        "advisory_only": True,
        "execution_authorized": False,
        "submission_authorized": False,
    }


def assess_reviewed_target(draft, review, hostname):
    digest = validate_draft(draft)

    if not isinstance(review, dict):
        raise ScopeReviewError("Missing review record")

    if (
        review.get("schema") != "jarvis.bounty.scope_review.r921b"
        or review.get("policy_sha256") != digest
        or review.get("platform") != draft["platform"]
        or review.get("program") != draft["program"]
        or review.get("review_status") != "operator_attested"
        or review.get("verification_method") != "manual_source_comparison"
        or review.get("advisory_only") is not True
        or review.get("execution_authorized") is not False
        or review.get("submission_authorized") is not False
        or not isinstance(review.get("reviewer"), str)
        or not review["reviewer"].strip()
    ):
        raise ScopeReviewError("Invalid review record")

    reviewed = utc_time(review["reviewed_at"])
    checked = utc_time(review["source_checked_at"])
    expires = utc_time(review["expires_at"])
    now = datetime.now(timezone.utc)

    if (
        reviewed > now + timedelta(minutes=5)
        or checked > reviewed + timedelta(minutes=5)
        or reviewed - checked > timedelta(days=1)
        or expires <= now
        or expires > reviewed + timedelta(days=7, minutes=1)
    ):
        raise ScopeReviewError("Review expired or time-invalid")

    result = assess_scope_target(draft, hostname)

    return {
        **result,
        "review_status": "operator_attested",
        "advisory_eligible": (
            result["classification"] ==
            "listed_in_unverified_draft"
        ),
        "testing_authorized": False,
        "execution_authorized": False,
        "human_review_required": True,
        "policy_sha256": digest,
    }
