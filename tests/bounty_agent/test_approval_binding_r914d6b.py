import sqlite3

import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_agent.autonomy.approvals import (
    ApprovalDenied,
    ApprovalStore,
)
from core.bounty_agent.autonomy.scheduler import MissionClaimStore


@pytest.fixture
def env(tmp_path):
    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="synthetic authorization",
        ttl=3600,
    )
    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite", auths
    )
    claims = MissionClaimStore(tmp_path / "claims.sqlite")
    return auths, auth, approvals, claims


def fields(auth):
    return dict(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="policy-v1",
    )


def approved_claim(env):
    _, auth, approvals, claims = env
    approval = approvals.issue(
        **fields(auth),
        budget=5,
        reviewer="tester",
    )
    assert approvals.verify(
        approval, **fields(auth), budget=5
    )
    result = claims.claim(
        **fields(auth), approval_id=approval
    )
    return approval, result


def test_new_claim_binds_approval(env):
    approval, result = approved_claim(env)
    assert result["acquired"] is True
    assert result["claim"]["approval_id"] == approval


def test_identical_retry(env):
    approval, first = approved_claim(env)
    _, auth, _, claims = env
    second = claims.claim(
        **fields(auth), approval_id=approval
    )
    assert second["acquired"] is False
    assert (
        second["claim"]["claim_key"]
        == first["claim"]["claim_key"]
    )


def test_different_approval_rejected(env):
    first, _ = approved_claim(env)
    _, auth, approvals, claims = env
    second = approvals.issue(
        **fields(auth),
        budget=5,
        reviewer="tester",
    )
    assert second != first
    with pytest.raises(sqlite3.IntegrityError):
        claims.claim(
            **fields(auth), approval_id=second
        )


def test_legacy_claim_cannot_be_upgraded(env):
    _, auth, approvals, claims = env
    claims.claim(**fields(auth))
    approval = approvals.issue(
        **fields(auth),
        budget=5,
        reviewer="tester",
    )
    with pytest.raises(sqlite3.IntegrityError):
        claims.claim(
            **fields(auth), approval_id=approval
        )


def test_approved_claim_rejects_legacy_retry(env):
    approved_claim(env)
    _, auth, _, claims = env
    with pytest.raises(sqlite3.IntegrityError):
        claims.claim(**fields(auth))


def test_revoked_approval_fails_verification(env):
    approval, _ = approved_claim(env)
    _, auth, approvals, _ = env
    approvals.revoke(approval)
    with pytest.raises(ApprovalDenied):
        approvals.verify(
            approval, **fields(auth), budget=5
        )


def test_binding_persists_after_restart(env):
    approval, _ = approved_claim(env)
    _, auth, _, claims = env
    reopened = MissionClaimStore(claims.path)
    result = reopened.claim(
        **fields(auth), approval_id=approval
    )
    assert result["acquired"] is False
    assert result["claim"]["approval_id"] == approval
