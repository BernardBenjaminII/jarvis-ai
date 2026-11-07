import sqlite3
import time

import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_agent.autonomy.approvals import (
    ApprovalDenied,
    ApprovalStore,
)


@pytest.fixture
def environment(tmp_path):
    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="reviewer",
        source_material="synthetic test policy",
        ttl=3600,
    )
    store = ApprovalStore(
        tmp_path / "approvals.sqlite", auths
    )
    return auths, auth, store


def fields(auth):
    return dict(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="policy-v1",
        budget=5,
    )


def issue(environment):
    _, auth, store = environment
    return store.issue(
        **fields(auth),
        reviewer="human-reviewer",
        ttl=600,
    )


def test_issue_and_verify(environment):
    _, auth, store = environment
    approval = issue(environment)
    assert store.verify(approval, **fields(auth)) is True


def test_restart_persistence(environment):
    auths, auth, store = environment
    approval = issue(environment)
    reopened = ApprovalStore(store.path, auths)
    assert reopened.verify(approval, **fields(auth))


def test_unknown_approval(environment):
    _, auth, store = environment
    with pytest.raises(ApprovalDenied):
        store.verify("unknown", **fields(auth))


def test_revoke_approval(environment):
    _, auth, store = environment
    approval = issue(environment)
    store.revoke(approval, "test revocation")
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **fields(auth))


def test_authorization_revocation(environment):
    auths, auth, store = environment
    approval = issue(environment)
    auths.revoke(auth)
    with pytest.raises(Exception):
        store.verify(approval, **fields(auth))


def test_budget_mismatch(environment):
    _, auth, store = environment
    approval = issue(environment)
    request = fields(auth)
    request["budget"] = 6
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **request)


def test_policy_mismatch(environment):
    _, auth, store = environment
    approval = issue(environment)
    request = fields(auth)
    request["policy_digest"] = "policy-v2"
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **request)


def test_target_mismatch(environment):
    _, auth, store = environment
    approval = issue(environment)
    request = fields(auth)
    request["target"] = "other.example"
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **request)


def test_expired_approval(environment):
    _, auth, store = environment
    approval = issue(environment)
    with store.db() as db:
        db.execute(
            "UPDATE approvals SET expires=? WHERE id=?",
            (time.time() - 1, approval),
        )
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **fields(auth))


def test_tampering_rejected(environment):
    _, auth, store = environment
    approval = issue(environment)
    with store.db() as db:
        db.execute(
            "UPDATE approvals SET reviewer=? WHERE id=?",
            ("forged-reviewer", approval),
        )
    with pytest.raises(ApprovalDenied):
        store.verify(approval, **fields(auth))


def test_invalid_target_issuance(environment):
    _, auth, store = environment
    request = fields(auth)
    request["target"] = "unauthorized.example"
    with pytest.raises(ApprovalDenied):
        store.issue(
            **request,
            reviewer="reviewer",
            ttl=600,
        )


def test_invalid_budget_issuance(environment):
    _, auth, store = environment
    request = fields(auth)
    request["budget"] = 100
    with pytest.raises(ApprovalDenied):
        store.issue(
            **request,
            reviewer="reviewer",
            ttl=600,
        )
