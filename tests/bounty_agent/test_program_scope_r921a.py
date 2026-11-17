"""R9.21A scope intake security checks."""

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    ScopeIntakeError,
    assess_scope_target,
    create_scope_draft,
)


@pytest.fixture
def draft():
    return create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=[
            "app.training.example",
            "api.training.example",
        ],
        out_of_scope=[
            "internal.training.example",
        ],
        restrictions=[
            "No denial-of-service testing",
            "No automated scanning without explicit approval",
        ],
    )


def test_draft_is_never_verified(draft):
    assert draft["scope_verified"] is False
    assert draft["review_status"] == "unverified"
    assert draft["execution_authorized"] is False
    assert draft["submission_authorized"] is False


def test_listed_target_requires_review(draft):
    result = assess_scope_target(
        draft, "api.training.example"
    )
    assert result["classification"] == (
        "listed_in_unverified_draft"
    )
    assert result["testing_authorized"] is False


def test_excluded_target_blocked(draft):
    result = assess_scope_target(
        draft, "internal.training.example"
    )
    assert result["classification"] == "explicitly_excluded"


def test_unknown_target_not_listed(draft):
    result = assess_scope_target(
        draft, "unknown.training.example"
    )
    assert result["classification"] == "not_listed"


def test_wildcard_rejected():
    with pytest.raises(ScopeIntakeError):
        create_scope_draft(
            platform="bugcrowd",
            program="Training",
            policy_url="https://bugcrowd.com/engagements/training",
            in_scope=["*.training.example"],
            out_of_scope=[],
            restrictions=["Manual review required"],
        )


def test_lookalike_policy_domain_rejected():
    with pytest.raises(ScopeIntakeError):
        create_scope_draft(
            platform="hackerone",
            program="Training",
            policy_url="https://hackerone.com.evil.example/program",
            in_scope=["app.training.example"],
            out_of_scope=[],
            restrictions=["Manual review required"],
        )


def test_digest_stable(draft):
    second = create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=[
            "api.training.example",
            "app.training.example",
        ],
        out_of_scope=["internal.training.example"],
        restrictions=[
            "No automated scanning without explicit approval",
            "No denial-of-service testing",
        ],
    )
    assert draft["policy_sha256"] == (
        second["policy_sha256"]
    )


def test_exclusion_overrides_inclusion():
    draft = create_scope_draft(
        platform="bugcrowd",
        program="Training",
        policy_url="https://bugcrowd.com/engagements/training",
        in_scope=["api.training.example"],
        out_of_scope=["api.training.example"],
        restrictions=["No automated testing"],
    )
    assert draft["in_scope"] == []
    assert assess_scope_target(
        draft, "api.training.example"
    )["classification"] == "explicitly_excluded"
