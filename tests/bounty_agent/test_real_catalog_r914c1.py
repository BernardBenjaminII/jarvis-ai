from core.bounty_agent.autonomy.approvals import ApprovalStore
from core.bounty_agent.autonomy.scheduler import MissionClaimStore
"""R9.14C.1 — Real catalog SQLite integration, offline."""

import json
import time

import pytest

import core.bounty_agent.engine as agent_engine
from core.bounty_agent.engine import BountyAgent
from core.bounty_agent.autonomy.catalog_controller import (
    plan_catalog_mission,
)
from core.bounty_authorization import AuthorizationStore
from core.bounty_catalog.store import Catalog
from core.bounty_catalog.opportunity import rank_catalog
from core.bounty_live import LiveMissionStore


def make_catalog(tmp_path, source="hackerone-api"):
    catalog = Catalog(tmp_path / "catalog.sqlite")

    payload = {
        "data": [
            {
                "type": "program",
                "attributes": {
                    "handle": "jarvis-training",
                    "name": "JARVIS Synthetic Training",
                    "offers_bounties": True,
                    "submission_state": "open",
                    "policy": (
                        "Synthetic training policy. "
                        "This is not real-world testing permission."
                    ),
                },
            }
        ],
        "links": {},
    }

    raw = json.dumps(payload).encode()

    catalog.save(
        source,
        time.time(),
        [(1, raw, time.time())],
        "complete" if source == "hackerone-api"
        else "local_import_unverified",
    )

    return catalog


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
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

    return auths, agent


def test_real_catalog_ranking(tmp_path):
    catalog = make_catalog(tmp_path)

    ranked = rank_catalog(catalog)

    assert "opportunities" in ranked
    assert any(
        item["handle"] == "jarvis-training"
        for item in ranked["opportunities"]
    )

    assert all(
        item["testing_authorized"] is False
        and item["execution_enabled"] is False
        for item in ranked["opportunities"]
    )


def test_real_catalog_without_approval_creates_no_mission(
    tmp_path, environment
):
    catalog = make_catalog(tmp_path)
    auths, agent = environment

    auths.create(
        program="jarvis-training",
        include=["training.example"],
        capabilities=["subfinder", "httpx"],
        reviewer="test-reviewer",
        source_material="synthetic test scope",
        ttl=3600,
    )

    result = plan_catalog_mission(
        catalog=catalog,
        authorization_store=auths,
        agent=agent,
        autonomous_approval_ids=(),
    )

    assert result.status == "no_authorized_candidate"
    assert agent.list_sessions() == []


def test_import_only_is_not_live_catalog(tmp_path):
    catalog = make_catalog(
        tmp_path,
        source="hackerone-import",
    )

    assert catalog.list()["programs"] == []


def test_real_catalog_creates_authorized_mission(
    tmp_path, environment
):
    catalog = Catalog(tmp_path / "positive_catalog.sqlite")
    auths, agent = environment

    raw = json.dumps({
        "data": [{
            "type": "program",
            "attributes": {
                "handle": "alpha",
                "name": "Alpha",
                "offers_bounties": True,
                "submission_state": "open",
                "state": "public_mode",
                "open_scope": True,
                "gold_standard_safe_harbor": True,
                "triage_active": True,
                "fast_payments": True,
                "policy": (
                    "Narrowly scoped scanners are allowed "
                    "against authorized assets. "
                    "Maximum bounty $10,000."
                ),
            },
        }],
        "links": {},
    }).encode()

    now = time.time()
    catalog.save(
        "hackerone-api",
        now,
        [(1, raw, now)],
        "complete",
    )

    authorization = auths.create(
        program="alpha",
        include=["training.example"],
        capabilities=["subfinder", "httpx"],
        reviewer="synthetic-test-reviewer",
        source_material="synthetic reviewed policy",
        ttl=3600,
    )

    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )
    claims = MissionClaimStore(tmp_path / "claims.sqlite")
    approval_id = approvals.issue(
        authorization=authorization,
        program="alpha",
        target="training.example",
        policy_digest="synthetic-alpha-policy-v1",
        budget=2,
        reviewer="synthetic-test-reviewer",
        ttl=600,
    )

    result = plan_catalog_mission(
        catalog=catalog,
        authorization_store=auths,
        agent=agent,
        claim_store=claims,
        approval_store=approvals,
        approval_id=approval_id,
        policy_digest="synthetic-alpha-policy-v1",
        budget=2,
    )

    assert result.status == "mission_created"
    assert result.program == "alpha"
    assert result.target == "training.example"
    assert result.authorization_id == authorization
    assert result.session_id
    assert result.mission_id

    report = agent.report(result.session_id)

    assert report["mission"]["tasks"] == []
    assert report["session"]["mission"] == result.mission_id
