import json

from core.bounty_agent.autonomy.hunter import (
    authorized,
    discover_programs,
    run_cycle,
)


def program(name, priority=10, verified=True):
    return {
        "id": name,
        "priority": priority,
        "active": True,
        "authorization_verified": verified,
        "simulation_only": True,
        "scope": [f"{name}.example"],
    }


def test_discovery_ranking():
    result = discover_programs([
        program("low", 1),
        program("high", 100),
    ])
    assert result[0]["id"] == "high"


def test_unverified_scope_rejected():
    assert not authorized(
        program("unverified", verified=False)
    )


def test_inactive_program_rejected():
    item = program("inactive")
    item["active"] = False
    assert not authorized(item)


def test_live_target_rejected():
    item = program("unsafe")
    item["scope"] = ["real-target.com"]
    assert not authorized(item)


def test_empty_scope_rejected():
    item = program("empty")
    item["scope"] = []
    assert not authorized(item)


def test_autonomous_selection(tmp_path):
    result = run_cycle([
        program("unverified", 100, False),
        program("eligible", 50, True),
    ], tmp_path)

    assert result["status"] == "awaiting_human_review"
    assert result["missions"][0]["program_id"] == "eligible"


def test_report_is_not_submitted(tmp_path):
    result = run_cycle(
        [program("eligible")], tmp_path
    )
    report = json.loads(
        open(result["report_path"]).read()
    )

    assert report["submission_authorized"] is False
    assert report["confirmed_vulnerabilities"] == 0
    assert all(
        not f["validated_vulnerability"]
        for f in report["findings"]
    )


def test_no_eligible_program(tmp_path):
    result = run_cycle([
        program("blocked", 100, False)
    ], tmp_path)

    assert result["status"] == "no_eligible_programs"
    assert result["missions"] == []
    assert list(tmp_path.iterdir()) == []
