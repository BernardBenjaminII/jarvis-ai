from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    ScopeReviewError,
    assess_reviewed_target,
    review_scope_draft,
)


@pytest.fixture
def draft():
    return create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["internal.training.example"],
        restrictions=["No automated scanning"],
    )


@pytest.fixture
def review(draft):
    return review_scope_draft(
        draft,
        reviewer="test-operator",
        source_checked_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source_matches=True,
    )


def test_review_still_disables_execution(review):
    assert review["advisory_only"] is True
    assert review["execution_authorized"] is False
    assert review["submission_authorized"] is False


def test_listed_target_advisory_only(draft, review):
    result = assess_reviewed_target(
        draft, review, "api.training.example"
    )
    assert result["advisory_eligible"] is True
    assert result["testing_authorized"] is False
    assert result["execution_authorized"] is False


def test_excluded_target_not_eligible(draft, review):
    result = assess_reviewed_target(
        draft, review, "internal.training.example"
    )
    assert result["advisory_eligible"] is False


def test_unknown_target_not_eligible(draft, review):
    result = assess_reviewed_target(
        draft, review, "unknown.training.example"
    )
    assert result["advisory_eligible"] is False


def test_scope_tampering_rejected(draft, review):
    modified = deepcopy(draft)
    modified["in_scope"].append("admin.training.example")
    with pytest.raises(ScopeReviewError):
        assess_reviewed_target(
            modified, review, "admin.training.example"
        )


def test_wrong_digest_rejected(draft, review):
    modified = deepcopy(review)
    modified["policy_sha256"] = "0" * 64
    with pytest.raises(ScopeReviewError):
        assess_reviewed_target(
            draft, modified, "api.training.example"
        )


def test_expired_review_rejected(draft, review):
    modified = deepcopy(review)
    modified["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(ScopeReviewError):
        assess_reviewed_target(
            draft, modified, "api.training.example"
        )


def test_no_attestation_rejected(draft):
    with pytest.raises(ScopeReviewError):
        review_scope_draft(
            draft,
            reviewer="test-operator",
            source_checked_at=datetime.now(
                timezone.utc
            ).isoformat(),
            source_matches=False,
        )


def test_review_does_not_mutate_draft(draft):
    original = deepcopy(draft)

    review_scope_draft(
        draft,
        reviewer="test-operator",
        source_checked_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source_matches=True,
    )

    assert draft == original
    assert draft["scope_verified"] is False
