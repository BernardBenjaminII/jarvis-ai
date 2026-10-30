import pytest

from core.bounty_agent.engine import BountyAgent
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore
import core.bounty_agent.engine as agent_engine
import core.bounty_live.engine as live_engine


def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_engine, "detect_platform", lambda: "kali")
    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    auth = auths.create(program="demo", include=["example.com", "*.example.com"], exclude=["private.example.com"], capabilities=["subfinder", "httpx"], reviewer="scope-reviewer", source_material="reviewed synthetic rules", ttl=3600)
    live = LiveMissionStore(tmp_path / "live.sqlite", authorization_store=auths)
    monkeypatch.setattr(live_engine, "enumerate_subdomains", lambda scope,target,cancel=None:{"adapter":"subfinder","target":target,"state":"completed","returncode":0,"accepted":["api.example.com","www.example.com"],"rejected":[]})
    monkeypatch.setattr(live_engine, "probe_http", lambda scope,target,cancel=None:{"adapter":"httpx","target":target,"state":"completed","returncode":0,"status_code":200,"title":"GraphQL API" if target.startswith("api.") else "Website","technology":["nginx","graphql"] if target.startswith("api.") else ["nginx"]})
    monkeypatch.setattr(live, "_tool_metadata", lambda capability:{"binary_path":f"/test/{capability}","tool_version":"test"})
    return auths, auth, BountyAgent(tmp_path / "agent.sqlite", authorization_store=auths, live_store=live)


def test_agent_runs_authorized_recon_to_human_gate(tmp_path, monkeypatch):
    _, auth, agent = environment(tmp_path, monkeypatch)
    sid = agent.create(auth, "example.com", budget=10)
    report = agent.run_recon(sid)
    assert report["session"]["state"] == "options_ready"
    assert len(report["options"]) == 3
    assert all(x["state"] == "awaiting_human" for x in report["options"])
    assert report["options"][0]["score"] >= report["options"][1]["score"]


def test_agent_pursue_is_decision_only(tmp_path, monkeypatch):
    _, auth, agent = environment(tmp_path, monkeypatch)
    sid = agent.create(auth, "example.com", budget=10)
    report = agent.run_recon(sid)
    option_id = report["options"][0]["id"]
    decided = agent.decide(option_id, "pursue", "human")
    assert decided["state"] == "pursue"
    mission = agent.report(sid)["mission"]
    capabilities = [x["capability"] for x in mission["tasks"]]
    assert set(capabilities) <= {"subfinder", "httpx"}


def test_agent_refuses_non_kali_live_start(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_engine, "detect_platform", lambda: "ubuntu")
    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    auth = auths.create(program="demo", include=["example.com"], capabilities=["subfinder", "httpx"], reviewer="scope-reviewer", source_material="rules", ttl=3600)
    live = LiveMissionStore(tmp_path / "live.sqlite", authorization_store=auths)
    agent = BountyAgent(tmp_path / "agent.sqlite", authorization_store=auths, live_store=live)
    with pytest.raises(Exception):
        agent.create(auth, "example.com")


def test_httpx_runs_on_authorized_root_when_subfinder_finds_nothing(
    tmp_path,
    monkeypatch,
):
    from core.bounty_agent import engine as agent_engine
    from core.bounty_authorization import AuthorizationStore
    from core.bounty_live import engine as live_engine

    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        path=tmp_path / "auth.sqlite"
    )

    authorization = auths.create(
        program="seed-test",
        include=["api.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="scope-reviewer",
        source_material="reviewed synthetic rules",
        ttl=3600,
    )

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [],
            "rejected": [],
        },
    )

    probed = []

    def fake_probe_http(scope, target, cancel=None):
        probed.append(target)

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "status_code": 200,
            "title": "Seed Target",
            "technology": [],
        }

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_probe_http,
    )

    agent = agent_engine.BountyAgent(
        path=tmp_path / "agent.sqlite",
        authorization_store=auths,
    )

    session = agent.create(
        authorization,
        "api.example.com",
        budget=10,
    )

    report = agent.run_recon(session)

    assert probed == ["api.example.com"]

    capabilities = [
        task["capability"]
        for task in report["mission"]["tasks"]
    ]

    assert capabilities == [
        "subfinder",
        "httpx",
    ]

    assert report["session"]["state"] == "options_ready"
    assert len(report["options"]) == 1
    assert report["options"][0]["target"] == "api.example.com"


def test_authorized_root_is_not_httpx_probed_twice_if_subfinder_returns_it(
    tmp_path,
    monkeypatch,
):
    from core.bounty_agent import engine as agent_engine
    from core.bounty_authorization import AuthorizationStore
    from core.bounty_live import engine as live_engine

    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        path=tmp_path / "auth.sqlite"
    )

    authorization = auths.create(
        program="dedup-test",
        include=["example.com", "*.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="scope-reviewer",
        source_material="reviewed synthetic rules",
        ttl=3600,
    )

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "example.com",
                "api.example.com",
            ],
            "rejected": [],
        },
    )

    probed = []

    def fake_probe_http(scope, target, cancel=None):
        probed.append(target)

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "status_code": 200,
            "title": target,
            "technology": [],
        }

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_probe_http,
    )

    agent = agent_engine.BountyAgent(
        path=tmp_path / "agent.sqlite",
        authorization_store=auths,
    )

    session = agent.create(
        authorization,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(session)

    assert sorted(probed) == [
        "api.example.com",
        "example.com",
    ]

    assert probed.count("example.com") == 1

    assert sorted(
        option["target"]
        for option in report["options"]
    ) == [
        "api.example.com",
        "example.com",
    ]


def test_dns_enabled_recon_only_http_probes_resolved_hosts(
    tmp_path,
    monkeypatch,
):
    """
    R8.8B:
    Native authorizations containing dns_resolution must
    route candidate hosts through DNSX before HTTPX.
    """
    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    authorization = auths.create(
        program="dns-gated-demo",
        include=[
            "example.com",
            "*.example.com",
        ],
        logical_capabilities=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        reviewer="scope-reviewer",
        source_material=(
            "reviewed synthetic DNS-gated rules"
        ),
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "api.example.com",
                "dead.example.com",
            ],
            "rejected": [],
        },
    )

    resolved = []

    def fake_resolve_dns(
        scope,
        target,
        cancel=None,
    ):
        resolved.append(target)

        accepted = (
            []
            if target == "dead.example.com"
            else [target]
        )

        return {
            "adapter": "dnsx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": accepted,
            "rejected": [],
            "records": (
                []
                if not accepted
                else [
                    {
                        "host": target,
                        "a": ["192.0.2.10"],
                    }
                ]
            ),
        }

    monkeypatch.setattr(
        live_engine,
        "resolve_dns",
        fake_resolve_dns,
    )

    probed = []

    def fake_probe_http(
        scope,
        target,
        cancel=None,
    ):
        probed.append(target)

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "status_code": 200,
            "title": target,
            "technology": [],
        }

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_probe_http,
    )

    monkeypatch.setattr(
        live,
        "_tool_metadata",
        lambda capability: {
            "binary_path": f"/test/{capability}",
            "tool_version": "test",
        },
    )

    agent = agent_engine.BountyAgent(
        path=tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    session = agent.create(
        authorization,
        "example.com",
        budget=20,
    )

    report = agent.run_recon(
        session
    )

    assert sorted(resolved) == [
        "api.example.com",
        "dead.example.com",
        "example.com",
    ]

    # dead.example.com did not resolve and therefore must
    # never reach HTTPX.
    assert sorted(probed) == [
        "api.example.com",
        "example.com",
    ]

    assert "dead.example.com" not in probed

    task_capabilities = [
        task["capability"]
        for task in report["mission"]["tasks"]
    ]

    assert task_capabilities.count(
        "subfinder"
    ) == 1

    assert task_capabilities.count(
        "dnsx"
    ) == 3

    assert task_capabilities.count(
        "httpx"
    ) == 2

    assert (
        report["mission"]["proposals"]
        == []
    )

    assert (
        report["session"]["state"]
        == "options_ready"
    )

    assert sorted(
        option["target"]
        for option in report["options"]
    ) == [
        "api.example.com",
        "example.com",
    ]


def test_legacy_authorization_does_not_invoke_dns(
    tmp_path,
    monkeypatch,
):
    """
    Existing R5/R8.7 authorizations must retain the
    pre-DNS execution path.
    """
    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    authorization = auths.create(
        program="legacy-no-dns",
        include=[
            "example.com",
            "*.example.com",
        ],
        capabilities=[
            "subfinder",
            "httpx",
        ],
        reviewer="scope-reviewer",
        source_material=(
            "legacy reviewed synthetic rules"
        ),
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "api.example.com",
            ],
            "rejected": [],
        },
    )

    def dns_must_not_run(*args, **kwargs):
        raise AssertionError(
            "Legacy authorization invoked DNS"
        )

    monkeypatch.setattr(
        live_engine,
        "resolve_dns",
        dns_must_not_run,
    )

    probed = []

    def fake_probe_http(
        scope,
        target,
        cancel=None,
    ):
        probed.append(target)

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "status_code": 200,
            "title": target,
            "technology": [],
        }

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_probe_http,
    )

    monkeypatch.setattr(
        live,
        "_tool_metadata",
        lambda capability: {
            "binary_path": f"/test/{capability}",
            "tool_version": "test",
        },
    )

    agent = agent_engine.BountyAgent(
        path=tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    session = agent.create(
        authorization,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(
        session
    )

    assert sorted(probed) == [
        "api.example.com",
        "example.com",
    ]

    capabilities = {
        task["capability"]
        for task in report["mission"]["tasks"]
    }

    assert capabilities <= {
        "subfinder",
        "httpx",
    }

    assert "dnsx" not in capabilities


def test_r912_dns_path_respects_target_budget(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        tmp_path / "auth-r912.sqlite"
    )

    authorization = auths.create(
        program="r912-demo",
        include=[
            "example.com",
            "*.example.com",
        ],
        logical_capabilities=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        reviewer="tester",
        source_material="r912 agent fixture",
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live-r912.sqlite",
        authorization_store=auths,
    )

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "a.example.com",
                "b.example.com",
                "c.example.com",
            ],
            "rejected": [],
        },
    )

    resolved = []

    def fake_dns(
        scope,
        target,
        cancel=None,
    ):
        resolved.append(target)

        return {
            "adapter": "dnsx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [target],
            "rejected": [],
            "records": [
                {
                    "host": target,
                    "a": ["192.0.2.10"],
                }
            ],
        }

    monkeypatch.setattr(
        live_engine,
        "resolve_dns",
        fake_dns,
    )

    probed = []

    def fake_http(
        scope,
        target,
        cancel=None,
    ):
        probed.append(target)

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "records": [
                {
                    "url":
                        f"https://{target}",
                    "status_code": 200,
                }
            ],
        }

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_http,
    )

    monkeypatch.setattr(
        live,
        "_tool_metadata",
        lambda capability: {
            "binary_path":
                f"/test/{capability}",
            "tool_version":
                "test",
        },
    )

    agent = agent_engine.BountyAgent(
        tmp_path / "agent-r912.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    session = agent.create(
        authorization,
        "example.com",
        budget=2,
    )

    report = agent.run_recon(
        session
    )

    # Root is always preserved. Only one discovered
    # hostname may join it under a 2-target budget.
    assert resolved == [
        "example.com",
        "a.example.com",
    ]

    assert sorted(probed) == [
        "a.example.com",
        "example.com",
    ]

    mission = report["mission"]["mission"]

    assert mission["budget"] == 2

    # 1 discovery + 2 DNS + 2 HTTP.
    assert mission["used"] == 5


def test_r92a_pursue_creates_non_executable_plan(
    tmp_path,
    monkeypatch,
):
    _, auth, agent = environment(
        tmp_path,
        monkeypatch,
    )

    session = agent.create(
        auth,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(
        session
    )

    option = report["options"][0]

    before_tasks = len(
        report["mission"]["tasks"]
    )

    decided = agent.decide(
        option["id"],
        "pursue",
        "human-reviewer",
    )

    assert decided["state"] == "pursue"

    after = agent.report(
        session
    )

    assert len(
        after["mission"]["tasks"]
    ) == before_tasks

    plans = after[
        "investigation_plans"
    ]

    assert len(plans) == 1

    plan = plans[0]["plan"]

    assert (
        plan["option_id"]
        == option["id"]
    )

    assert (
        plan["target"]
        == option["target"]
    )

    assert (
        plan["state"]
        == "awaiting_action_approval"
    )

    assert (
        plan["automatic_execution_allowed"]
        is False
    )

    assert (
        plan["scope_expansion_allowed"]
        is False
    )

    assert (
        plan["vulnerability_validation_allowed"]
        is False
    )

    assert (
        plan["report_submission_allowed"]
        is False
    )

    assert plan["proposed_actions"]

    assert all(
        action["execution_allowed"]
        is False
        for action
        in plan["proposed_actions"]
    )


def test_r92a_hold_does_not_create_plan(
    tmp_path,
    monkeypatch,
):
    _, auth, agent = environment(
        tmp_path,
        monkeypatch,
    )

    session = agent.create(
        auth,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(
        session
    )

    agent.decide(
        report["options"][0]["id"],
        "hold",
        "human-reviewer",
    )

    assert (
        agent.report(
            session
        )["investigation_plans"]
        == []
    )


def test_r92a_repeated_pursue_is_idempotent(
    tmp_path,
    monkeypatch,
):
    _, auth, agent = environment(
        tmp_path,
        monkeypatch,
    )

    session = agent.create(
        auth,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(
        session
    )

    option_id = (
        report["options"][0]["id"]
    )

    agent.decide(
        option_id,
        "pursue",
        "reviewer-a",
    )

    agent.decide(
        option_id,
        "pursue",
        "reviewer-b",
    )

    plans = agent.report(
        session
    )["investigation_plans"]

    assert len(plans) == 1

    assert (
        plans[0]["reviewer"]
        == "reviewer-b"
    )


def _r93_plan_environment(
    tmp_path,
    monkeypatch,
):
    _, auth, agent = environment(
        tmp_path,
        monkeypatch,
    )

    session = agent.create(
        auth,
        "example.com",
        budget=10,
    )

    report = agent.run_recon(
        session
    )

    before_tasks = len(
        report["mission"]["tasks"]
    )

    agent.decide(
        report["options"][0]["id"],
        "pursue",
        "human-reviewer",
    )

    report = agent.report(
        session
    )

    plan_wrapper = (
        report[
            "investigation_plans"
        ][0]
    )

    return (
        agent,
        session,
        plan_wrapper,
        before_tasks,
    )


def test_r93_action_approval_is_persisted_but_nonexecuting(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        session,
        wrapper,
        before_tasks,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    plan_id = wrapper["id"]

    action_id = (
        wrapper["plan"]
        ["proposed_actions"][0]
        ["id"]
    )

    result = agent.decide_plan_action(
        plan_id,
        action_id,
        "approve",
        "action-reviewer",
    )

    action = next(
        action
        for action
        in result["plan"]["proposed_actions"]
        if action["id"] == action_id
    )

    assert (
        action["approval_state"]
        == "approved"
    )

    assert (
        action["reviewer"]
        == "action-reviewer"
    )

    assert (
        action["execution_allowed"]
        is False
    )

    assert (
        result["plan"][
            "automatic_execution_allowed"
        ]
        is False
    )

    after = agent.report(
        session
    )

    assert len(
        after["mission"]["tasks"]
    ) == before_tasks


def test_r93_action_rejection_is_persisted(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action_id = (
        wrapper["plan"]
        ["proposed_actions"][0]
        ["id"]
    )

    result = agent.decide_plan_action(
        wrapper["id"],
        action_id,
        "reject",
        "reviewer-r",
    )

    action = next(
        action
        for action
        in result["plan"]["proposed_actions"]
        if action["id"] == action_id
    )

    assert (
        action["approval_state"]
        == "rejected"
    )

    assert (
        action["execution_allowed"]
        is False
    )


def test_r93_unknown_action_is_rejected(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    with pytest.raises(Exception):
        agent.decide_plan_action(
            wrapper["id"],
            "step-999",
            "approve",
            "reviewer",
        )


def test_r93_all_action_decisions_complete_plan_state(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    current = wrapper

    for action in (
        wrapper["plan"]
        ["proposed_actions"]
    ):
        current = agent.decide_plan_action(
            wrapper["id"],
            action["id"],
            "approve",
            "reviewer",
        )

    assert (
        current["plan"]["state"]
        == "action_decisions_complete"
    )

    assert all(
        action["execution_allowed"]
        is False
        for action
        in current["plan"][
            "proposed_actions"
        ]
    )


def test_r94_human_review_proposal_requires_no_execution(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        session,
        wrapper,
        before_tasks,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    result = agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "proposal-reviewer",
    )

    proposal = next(
        item["execution_proposal"]
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    assert (
        proposal["proposal_state"]
        == "ready_for_manual_review"
    )

    assert (
        proposal[
            "new_tool_execution_required"
        ]
        is False
    )

    assert (
        proposal["execution_allowed"]
        is False
    )

    after = agent.report(session)

    assert len(
        after["mission"]["tasks"]
    ) == before_tasks


def test_r94_unapproved_action_cannot_get_proposal(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][1]
    )

    with pytest.raises(Exception):
        agent.propose_plan_action(
            wrapper["id"],
            action["id"],
            "reviewer",
        )


def test_r94_unauthorized_capability_is_blocked(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][1]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    result = agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "proposal-reviewer",
    )

    proposal = next(
        item["execution_proposal"]
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    assert (
        proposal["proposal_state"]
        == "authorization_required"
    )

    assert (
        proposal["capability_authorized"]
        is False
    )

    assert (
        proposal["authorization_required"]
        is True
    )

    assert (
        proposal["execution_allowed"]
        is False
    )


def test_r95_manual_evidence_review_uses_existing_evidence_only(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        session,
        wrapper,
        before_tasks,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "proposal-reviewer",
    )

    result = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "evidence-reviewer",
    )

    selected = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    review = selected["evidence_review"]

    assert (
        review["classification"]
        == "recon_lead_not_vulnerability"
    )

    assert (
        review["new_network_traffic"]
        is False
    )

    assert (
        review["new_live_tasks_created"]
        is False
    )

    assert (
        review["execution_allowed"]
        is False
    )

    assert review["observations"]

    after = agent.report(session)

    assert len(
        after["mission"]["tasks"]
    ) == before_tasks


def test_r95_review_requires_approved_action(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    with pytest.raises(Exception):
        agent.review_plan_action_evidence(
            wrapper["id"],
            action["id"],
            "reviewer",
        )


def test_r95_review_requires_r94_proposal(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    with pytest.raises(Exception):
        agent.review_plan_action_evidence(
            wrapper["id"],
            action["id"],
            "reviewer",
        )


def test_r95_review_preserves_execution_lock(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    result = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    assert (
        selected["execution_allowed"]
        is False
    )

    assert (
        result["plan"][
            "automatic_execution_allowed"
        ]
        is False
    )


def test_r96_select_hypothesis_persists_human_decision(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = (
        wrapper["plan"]
        ["proposed_actions"][0]
    )

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action[
            "evidence_review"
        ]["hypotheses"][0]
    )

    result = agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    selected_action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    review = selected_action["evidence_review"]

    selected = next(
        item
        for item
        in review["hypotheses"]
        if item["id"] == hypothesis["id"]
    )

    assert selected["selection_state"] == "selected"
    assert selected["selected_by"] == "abdullah"

    assert (
        selected["validation_state"]
        == "awaiting_validation_authorization"
    )

    assert selected["validation_authorized"] is False
    assert selected["execution_allowed"] is False

    assert (
        review["selected_hypothesis_id"]
        == hypothesis["id"]
    )

    assert (
        review["recommended_next_state"]
        == "validation_authorization_required"
    )


def test_r96_hold_hypothesis_does_not_request_validation(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    result = agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "hold",
        "abdullah",
    )

    selected_action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    held = next(
        item
        for item
        in selected_action[
            "evidence_review"
        ]["hypotheses"]
        if item["id"] == hypothesis["id"]
    )

    assert held["selection_state"] == "held"
    assert held["validation_state"] == "not_requested"
    assert held["execution_allowed"] is False


def test_r96_reject_hypothesis_preserves_execution_lock(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    result = agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "reject",
        "abdullah",
    )

    selected_action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    rejected = next(
        item
        for item
        in selected_action[
            "evidence_review"
        ]["hypotheses"]
        if item["id"] == hypothesis["id"]
    )

    assert rejected["selection_state"] == "rejected"
    assert rejected["validation_state"] == "not_requested"

    assert (
        result["plan"]["vulnerability_validation_allowed"]
        is False
    )

    assert (
        result["plan"]["automatic_execution_allowed"]
        is False
    )


def test_r96_requires_existing_evidence_review(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    with pytest.raises(Exception):
        agent.decide_evidence_hypothesis(
            wrapper["id"],
            action["id"],
            "H1",
            "select",
            "abdullah",
        )


def test_r97_validation_proposal_requires_selected_hypothesis(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    with pytest.raises(Exception):
        agent.propose_validation_authorization(
            wrapper["id"],
            action["id"],
            hypothesis["id"],
            "abdullah",
        )


def test_r97_missing_parent_capability_stays_locked(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    result = agent.propose_validation_authorization(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "abdullah",
    )

    selected_action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    selected = next(
        item
        for item
        in selected_action[
            "evidence_review"
        ]["hypotheses"]
        if item["id"] == hypothesis["id"]
    )

    proposal = selected[
        "validation_authorization_proposal"
    ]

    assert (
        proposal["proposal_state"]
        == "parent_capability_authorization_required"
    )

    assert proposal["capability_authorized"] is False
    assert proposal["validation_authorized"] is False
    assert proposal["execution_allowed"] is False

    assert selected["validation_authorized"] is False
    assert selected["execution_allowed"] is False

    assert (
        result["plan"][
            "vulnerability_validation_allowed"
        ]
        is False
    )

    assert (
        result["plan"][
            "automatic_execution_allowed"
        ]
        is False
    )


def test_r97_validation_proposal_is_narrowly_bounded(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    result = agent.propose_validation_authorization(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "abdullah",
        request_budget=7,
        ttl=900,
    )

    selected_action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    selected = next(
        item
        for item
        in selected_action[
            "evidence_review"
        ]["hypotheses"]
        if item["id"] == hypothesis["id"]
    )

    proposal = selected[
        "validation_authorization_proposal"
    ]

    assert proposal["request_budget"] == 7
    assert proposal["ttl_seconds"] == 900

    assert proposal["allowed_methods"] == [
        "GET",
        "HEAD",
    ]

    assert proposal["scope"]["include"] == [
        result["plan"]["target"]
    ]

    assert (
        proposal["scope"][
            "scope_expansion_allowed"
        ]
        is False
    )

    assert (
        proposal["scope"][
            "cross_scope_redirect_following"
        ]
        is False
    )

    assert (
        "authentication_bypass"
        in proposal["prohibited"]
    )

    assert (
        "destructive_actions"
        in proposal["prohibited"]
    )


def test_r97_validation_budget_limits(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    with pytest.raises(Exception):
        agent.propose_validation_authorization(
            wrapper["id"],
            action["id"],
            hypothesis["id"],
            "abdullah",
            request_budget=26,
        )

    with pytest.raises(Exception):
        agent.propose_validation_authorization(
            wrapper["id"],
            action["id"],
            hypothesis["id"],
            "abdullah",
            ttl=3601,
        )


def _r97_selected_hypothesis_with_validation_proposal(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    proposed = agent.propose_validation_authorization(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "abdullah",
    )

    return (
        agent,
        proposed,
        action["id"],
        hypothesis["id"],
    )


def test_r97d_policy_permit_still_does_not_authorize_validation(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        wrapper,
        action_id,
        hypothesis_id,
    ) = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    result = agent.review_validation_capability_policy(
        wrapper["id"],
        action_id,
        hypothesis_id,
        "abdullah",
        decision="permit",
        policy_source="program policy",
        policy_evidence=(
            "Program policy permits bounded automated "
            "web crawling within reviewed staging scope."
        ),
        constraints=[
            "staging only",
            "low request rate",
        ],
    )

    action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action_id
    )

    hypothesis = next(
        item
        for item
        in action["evidence_review"]["hypotheses"]
        if item["id"] == hypothesis_id
    )

    proposal = hypothesis[
        "validation_authorization_proposal"
    ]

    review = proposal[
        "capability_policy_review"
    ]

    assert review["decision"] == "permit"

    assert (
        review["policy_state"]
        == "capability_policy_reviewed"
    )

    assert (
        proposal["proposal_state"]
        == "capability_policy_reviewed"
    )

    assert proposal["validation_authorized"] is False
    assert proposal["execution_allowed"] is False

    assert hypothesis["validation_authorized"] is False
    assert hypothesis["execution_allowed"] is False

    assert (
        result["plan"][
            "vulnerability_validation_allowed"
        ]
        is False
    )

    assert (
        result["plan"][
            "automatic_execution_allowed"
        ]
        is False
    )


def test_r97d_policy_deny_stays_locked(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        wrapper,
        action_id,
        hypothesis_id,
    ) = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    result = agent.review_validation_capability_policy(
        wrapper["id"],
        action_id,
        hypothesis_id,
        "abdullah",
        decision="deny",
        policy_source="program policy",
        policy_evidence=(
            "Program policy prohibits automated crawling."
        ),
    )

    action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action_id
    )

    hypothesis = next(
        item
        for item
        in action["evidence_review"]["hypotheses"]
        if item["id"] == hypothesis_id
    )

    proposal = hypothesis[
        "validation_authorization_proposal"
    ]

    assert (
        proposal["proposal_state"]
        == "capability_policy_denied"
    )

    assert proposal["validation_authorized"] is False
    assert proposal["execution_allowed"] is False


def test_r97d_policy_unclear_stays_locked(
    tmp_path,
    monkeypatch,
):
    (
        agent,
        wrapper,
        action_id,
        hypothesis_id,
    ) = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    result = agent.review_validation_capability_policy(
        wrapper["id"],
        action_id,
        hypothesis_id,
        "abdullah",
        decision="unclear",
        policy_source="program policy",
        policy_evidence=(
            "Policy does not explicitly address crawling."
        ),
    )

    action = next(
        item
        for item
        in result["plan"]["proposed_actions"]
        if item["id"] == action_id
    )

    hypothesis = next(
        item
        for item
        in action["evidence_review"]["hypotheses"]
        if item["id"] == hypothesis_id
    )

    proposal = hypothesis[
        "validation_authorization_proposal"
    ]

    assert (
        proposal["proposal_state"]
        == "capability_policy_unclear"
    )

    assert proposal["validation_authorized"] is False
    assert proposal["execution_allowed"] is False


def test_r97d_policy_review_requires_existing_validation_proposal(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        _,
        wrapper,
        _,
    ) = _r93_plan_environment(
        tmp_path,
        monkeypatch,
    )

    action = wrapper["plan"]["proposed_actions"][0]

    agent.decide_plan_action(
        wrapper["id"],
        action["id"],
        "approve",
        "reviewer",
    )

    agent.propose_plan_action(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    reviewed = agent.review_plan_action_evidence(
        wrapper["id"],
        action["id"],
        "reviewer",
    )

    selected_action = next(
        item
        for item
        in reviewed["plan"]["proposed_actions"]
        if item["id"] == action["id"]
    )

    hypothesis = (
        selected_action["evidence_review"]
        ["hypotheses"][0]
    )

    agent.decide_evidence_hypothesis(
        wrapper["id"],
        action["id"],
        hypothesis["id"],
        "select",
        "abdullah",
    )

    with pytest.raises(Exception):
        agent.review_validation_capability_policy(
            wrapper["id"],
            action["id"],
            hypothesis["id"],
            "abdullah",
            decision="permit",
            policy_source="program policy",
            policy_evidence="reviewed",
        )


def test_r97d_policy_review_rejects_invalid_decision(
    tmp_path,
    monkeypatch,
):
    import pytest

    (
        agent,
        wrapper,
        action_id,
        hypothesis_id,
    ) = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    with pytest.raises(Exception):
        agent.review_validation_capability_policy(
            wrapper["id"],
            action_id,
            hypothesis_id,
            "abdullah",
            decision="approve",
            policy_source="program policy",
            policy_evidence="reviewed",
        )


def test_r98a_portfolio_returns_analysis_only(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    assert result["schema"] == (
        "jarvis-bounty-opportunity-portfolio-r9.8a"
    )
    assert result["session"] == session_id
    assert result["reviewer"] == "abdullah"

    assert result["new_network_traffic"] is False
    assert result["tools_executed"] is False
    assert result["automatic_execution_enabled"] is False
    assert result["payout_ranking_enabled"] is False


def test_r98a_portfolio_never_marks_execution_allowed(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    assert result["opportunities"]

    for item in result["opportunities"]:
        assert item["execution_allowed"] is False
        assert item["scope_expansion_allowed"] is False
        assert item["automatic_execution_ready"] is False


def test_r98a_unclear_policy_penalizes_automation(tmp_path, monkeypatch):
    (
        agent,
        wrapper,
        action_id,
        hypothesis_id,
    ) = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = wrapper["session"]

    agent.review_validation_capability_policy(
        wrapper["id"],
        action_id,
        hypothesis_id,
        "abdullah",
        decision="unclear",
        policy_source="test policy",
        policy_evidence="crawler permission is unclear",
        constraints=["staging only"],
    )

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    target_name = wrapper.get("target")

    if not target_name:
        target_name = wrapper["plan"]["target"]

    target = next(
        item
        for item in result["opportunities"]
        if item["target"] == target_name
    )

    assert target["policy_state"] == "capability_policy_unclear"
    assert "web_crawling" in target["capability_gaps"]
    assert target["lane"] in {
        "MANUAL_A",
        "BLOCKED",
    }


def test_r98a_operator_brief_contains_manual_guidance(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    assert result["opportunities"]

    brief = result["opportunities"][0]["operator_brief"]

    assert brief["hunt_themes"]
    assert brief["what_to_capture"]
    assert brief["stop_conditions"]
    assert brief["report_quality_check"]


def test_r98a_lane_counts_match_opportunities(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    counted = {}

    for item in result["opportunities"]:
        counted[item["lane"]] = (
            counted.get(item["lane"], 0)
            + 1
        )

    assert counted == result["lane_counts"]


def test_r98a_portfolio_sorted_by_lane_and_value(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    lane_order = {
        "AUTO_A": 0,
        "AUTO_B": 1,
        "MANUAL_A": 2,
        "MANUAL_B": 3,
        "BLOCKED": 4,
        "SKIP": 5,
    }

    observed = [
        (
            lane_order[item["lane"]],
            -max(
                item["automation_viability_score"],
                item["manual_hunt_viability_score"],
            ),
            -item["recon_score"],
            item["target"],
        )
        for item in result["opportunities"]
    ]

    assert observed == sorted(observed)


def test_r98a_payout_data_explicitly_not_integrated(tmp_path, monkeypatch):
    agent, session_record, *_ = _r97_selected_hypothesis_with_validation_proposal(
        tmp_path,
        monkeypatch,
    )

    session_id = session_record["session"]

    result = agent.opportunity_portfolio(
        session_id,
        reviewer="abdullah",
    )

    assert result["payout_ranking_enabled"] is False

    for item in result["opportunities"]:
        assert item["payout_score"] is None
        assert item["payout_data_state"] == "not_yet_integrated"


def test_explicit_seed_mode_dnsx_then_httpx_without_subfinder(
    tmp_path,
    monkeypatch,
):
    """
    R9.10L.4

    An authorization containing only DNS resolution + HTTP
    probing must be able to operate on an explicitly reviewed
    hostname without invoking Subfinder.
    """

    from core.bounty_agent.engine import BountyAgent
    from core.bounty_authorization.store import AuthorizationStore
    from core.bounty_live import LiveMissionStore
    import core.bounty_live.engine as live_engine

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    auth_id = auths.create(
        program="seed-demo",
        include=[
            "api.example.com",
        ],
        exclude=[],
        logical_capabilities=[
            "dns_resolution",
            "http_probe",
        ],
        capabilities=[
            "dnsx",
            "httpx",
        ],
        reviewer="scope-reviewer",
        source_material=(
            "Reviewed explicit-host synthetic scope"
        ),
        ttl=3600,
    )

    calls = []

    def forbidden_subfinder(
        scope,
        target,
        cancel=None,
    ):
        raise AssertionError(
            "Subfinder must not run in explicit-seed mode"
        )

    def fake_dnsx(
        scope,
        target,
        cancel=None,
    ):
        calls.append(
            ("dnsx", target)
        )

        return {
            "adapter": "dnsx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": [
                target,
            ],
            "rejected": [],
        }

    def fake_httpx(
        scope,
        target,
        cancel=None,
    ):
        calls.append(
            ("httpx", target)
        )

        return {
            "adapter": "httpx",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "status_code": 200,
            "title": "Explicit Seed",
            "technology": [
                "synthetic",
            ],
        }

    monkeypatch.setattr(
        live_engine,
        "enumerate_subdomains",
        forbidden_subfinder,
    )

    monkeypatch.setattr(
        live_engine,
        "resolve_dns",
        fake_dnsx,
    )

    monkeypatch.setattr(
        live_engine,
        "probe_http",
        fake_httpx,
    )

    agent = BountyAgent(
        tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    monkeypatch.setattr(
        "core.bounty_agent.engine.detect_platform",
        lambda: "kali",
    )

    session = agent.create(
        auth_id,
        "api.example.com",
        budget=4,
    )

    report = agent.run_recon(
        session
    )

    assert (
        ("dnsx", "api.example.com")
        in calls
    )

    assert (
        ("httpx", "api.example.com")
        in calls
    )

    assert all(
        name != "subfinder"
        for name, _ in calls
    )

    assert report["session"]["state"] == "options_ready"

    capabilities = [
        task["capability"]
        for task in report["mission"]["tasks"]
    ]

    assert "dnsx" in capabilities
    assert "httpx" in capabilities
    assert "subfinder" not in capabilities


def test_explicit_seed_mode_rejects_wildcard_only_seed(
    tmp_path,
    monkeypatch,
):
    """
    A wildcard match is insufficient to start explicit-seed
    mode. The hostname itself must occur literally in the
    reviewed include list.
    """

    import pytest

    from core.bounty_agent.engine import (
        BountyAgent,
        BountyAgentError,
    )
    from core.bounty_authorization.store import AuthorizationStore
    from core.bounty_live import LiveMissionStore

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    auth_id = auths.create(
        program="seed-demo",
        include=[
            "*.example.com",
        ],
        exclude=[],
        logical_capabilities=[
            "dns_resolution",
            "http_probe",
        ],
        capabilities=[
            "dnsx",
            "httpx",
        ],
        reviewer="scope-reviewer",
        source_material=(
            "Wildcard-only synthetic scope"
        ),
        ttl=3600,
    )

    agent = BountyAgent(
        tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    monkeypatch.setattr(
        "core.bounty_agent.engine.detect_platform",
        lambda: "kali",
    )

    with pytest.raises(
        BountyAgentError,
        match=(
            "explicitly reviewed hostname"
        ),
    ):
        agent.create(
            auth_id,
            "api.example.com",
            budget=4,
        )
