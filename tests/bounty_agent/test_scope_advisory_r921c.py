from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    ScopeReviewError,
    review_scope_draft,
)
from core.bounty_agent.autonomy.scope_advisory_r921c import (
    build_scope_advisory,
)


@pytest.fixture
def context():
    draft = create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["internal.training.example"],
        restrictions=[
            "No automated scanning without explicit approval"
        ],
    )

    review = review_scope_draft(
        draft,
        reviewer="test-operator",
        source_checked_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source_matches=True,
    )

    tools = {
        "subfinder": {"executable_present": True},
        "amass": {"executable_present": False},
        "dnsx": {"executable_present": True},
        "httpx": {"recon_available": True},
    }

    return draft, review, tools


def build(context, target="api.training.example"):
    draft, review, tools = context

    return build_scope_advisory(
        draft=draft,
        review=review,
        target=target,
        tool_inventory=tools,
    )


def test_listed_target(context):
    result = build(context)

    assert result["advisory_eligible"] is True
    assert result["target"] == "api.training.example"
    assert result["execution_authorized"] is False


def test_excluded_target(context):
    result = build(
        context, "internal.training.example"
    )

    assert result["advisory_eligible"] is False
    assert result["target_classification"] == (
        "explicitly_excluded"
    )


def test_unknown_target(context):
    result = build(
        context, "unknown.training.example"
    )

    assert result["advisory_eligible"] is False


def test_available_tools_do_not_grant_permission(context):
    result = build(context)

    assert result["policy_permissions_verified"] is False
    assert result["testing_authorized"] is False
    assert result["submission_authorized"] is False

    assert all(
        activity["activity_permission"] == "not_established"
        and activity["execution_allowed"] is False
        and activity["human_review_required"] is True
        for activity in result["activities"]
    )


def test_httpx_identity_check(context):
    draft, review, tools = context
    tools["httpx"] = {
        "executable_present": True,
        "recon_available": False,
    }

    result = build(context)

    http = next(
        item for item in result["activities"]
        if item["capability"] == "http_probe"
    )

    assert http["tools"][0]["detected"] is False


def test_expired_review_rejected(context):
    draft, review, tools = context
    expired = deepcopy(review)

    expired["expires_at"] = (
        datetime.now(timezone.utc) -
        timedelta(seconds=1)
    ).isoformat()

    with pytest.raises(ScopeReviewError):
        build_scope_advisory(
            draft=draft,
            review=expired,
            target="api.training.example",
            tool_inventory=tools,
        )


def test_tampered_scope_rejected(context):
    draft, review, tools = context
    changed = deepcopy(draft)
    changed["in_scope"].append(
        "admin.training.example"
    )

    with pytest.raises(ScopeReviewError):
        build_scope_advisory(
            draft=changed,
            review=review,
            target="admin.training.example",
            tool_inventory=tools,
        )


def test_invalid_inventory_rejected(context):
    draft, review, _ = context

    with pytest.raises(ValueError):
        build_scope_advisory(
            draft=draft,
            review=review,
            target="api.training.example",
            tool_inventory=[],
        )
