"""R9.14D.5C: offline coordinator integration tests."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from core.bounty_agent.autonomy.approvals import (
    ApprovalDenied,
    ApprovalStore,
)

from core.bounty_agent import engine as agent_engine
from core.bounty_agent.engine import BountyAgent
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore
from core.bounty_agent.autonomy.scheduler import MissionClaimStore
from core.bounty_agent.autonomy.coordinator import (
    CoordinationError,
    coordinate_mission,
)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine, "detect_platform", lambda: "kali"
    )

    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="synthetic authorization",
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )
    agent = BountyAgent(
        tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )
    claims = MissionClaimStore(tmp_path / "claims.sqlite")
    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )
    approval_id = approvals.issue(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="synthetic-policy-v1",
        budget=5,
        reviewer="tester",
        ttl=600,
    )

    return auth, live, agent, claims, approvals, approval_id


def request(environment, **overrides):
    auth, _, agent, claims, approvals, approval_id = environment

    arguments = {
        "claim_store": claims,
        "agent": agent,
        "authorization": auth,
        "program": "training",
        "target": "training.example",
        "policy_digest": "synthetic-policy-v1",
        "budget": 5,
        "approval_store": approvals,
        "approval_id": approval_id,
    }
    arguments.update(overrides)
    return arguments


def counts(environment):
    _, live, agent, claims, _, _ = environment

    with live.db() as db:
        missions = db.execute(
            "SELECT COUNT(*) FROM missions"
        ).fetchone()[0]

    with agent.db() as db:
        sessions = db.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

    with claims.connect() as db:
        claims_count = db.execute(
            "SELECT COUNT(*) FROM claims"
        ).fetchone()[0]

    return missions, sessions, claims_count


def test_first_creation(environment):
    result = coordinate_mission(**request(environment))

    assert result.status == "mission_created"
    assert result.session_id
    assert result.mission_id
    assert counts(environment) == (1, 1, 1)


def test_identical_retry(environment):
    first = coordinate_mission(**request(environment))
    second = coordinate_mission(**request(environment))

    assert second.status == "already_created"
    assert second.session_id == first.session_id
    assert second.mission_id == first.mission_id
    assert counts(environment) == (1, 1, 1)


def test_missing_approval_rejected(environment):
    arguments = request(
        environment, approval_id=None
    )

    with pytest.raises(CoordinationError):
        coordinate_mission(**arguments)

    assert counts(environment) == (0, 0, 0)


def test_denied_approval_rejected(environment):
    arguments = request(
        environment,
        approval_id='nonexistent-approval',
    )

    with pytest.raises(ApprovalDenied):
        coordinate_mission(**arguments)

    assert counts(environment) == (0, 0, 0)


def test_concurrent_creation(environment):
    arguments = request(environment)

    def create(_):
        return coordinate_mission(**arguments)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(create, range(12)))

    assert len({r.session_id for r in results}) == 1
    assert len({r.mission_id for r in results}) == 1
    assert counts(environment) == (1, 1, 1)


def test_recover_after_mission_only(environment):
    auth, live, _, claims, _, approval_id = environment
    arguments = request(environment)

    key = claims.key(
        auth,
        "training",
        "training.example",
        "synthetic-policy-v1",
    )

    claims.claim(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="synthetic-policy-v1",
        approval_id=approval_id,
    )

    existing_mid = live.create(
        auth, budget=5, operation_id=key
    )

    result = coordinate_mission(**arguments)

    assert result.mission_id == existing_mid
    assert counts(environment) == (1, 1, 1)


def test_recover_after_session_creation(environment):
    auth, _, agent, claims, _, approval_id = environment
    arguments = request(environment)

    key = claims.key(
        auth,
        "training",
        "training.example",
        "synthetic-policy-v1",
    )

    claims.claim(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="synthetic-policy-v1",
        approval_id=approval_id,
    )

    existing_sid = agent.create(
        auth,
        "training.example",
        budget=5,
        operation_id=key,
    )

    result = coordinate_mission(**arguments)

    assert result.session_id == existing_sid
    assert counts(environment) == (1, 1, 1)


def test_created_claim_missing_session_fails_closed(environment):
    result = coordinate_mission(**request(environment))
    _, _, agent, _, _, _ = environment

    with agent.db() as db:
        db.execute(
            "DELETE FROM sessions WHERE id=?",
            (result.session_id,),
        )

    with pytest.raises(CoordinationError):
        coordinate_mission(**request(environment))


def test_changed_budget_rejected(environment):
    coordinate_mission(**request(environment))

    with pytest.raises(ApprovalDenied):
        coordinate_mission(
            **request(environment, budget=6)
        )

    assert counts(environment) == (1, 1, 1)


def test_cross_policy_conflict(environment):
    coordinate_mission(**request(environment))

    with pytest.raises(Exception):
        coordinate_mission(
            **request(
                environment,
                policy_digest="synthetic-policy-v2",
            )
        )

    assert counts(environment) == (1, 1, 1)
