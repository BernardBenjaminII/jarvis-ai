import pytest

from core.bounty_agent.autonomy.mission_advisory_r920d import (
    build_mission_advisory,
)
from core.bounty_agent.autonomy.recon_planner import (
    ReconPlanningError,
)


class Scope:
    program = "training"
    logical_capabilities = (
        "subdomain_discovery",
        "dns_resolution",
        "http_probe",
    )

    def permits_host(self, host):
        return host == "training.example"

    def require(self, host, tool):
        if not self.permits_host(host):
            raise ValueError("Target not permitted")
        if tool not in {"subfinder", "dnsx", "httpx"}:
            raise ValueError("Tool not permitted")


class Store:
    def live_scope(self, authorization_id):
        if authorization_id != "auth-test":
            raise ValueError("Unknown authorization")
        return Scope()


@pytest.fixture
def args():
    return {
        "authorization_store": Store(),
        "authorization_id": "auth-test",
        "program": "training",
        "target": "training.example",
        "budget": 3,
        "tool_inventory": {
            "subfinder": {"executable_present": True},
            "dnsx": {"executable_present": True},
            "httpx": {"recon_available": True},
        },
    }


def test_approved_synthetic_plan(args):
    result = build_mission_advisory(**args)

    assert result["authorization_checked"] is True
    assert result["execution_authorized"] is False
    assert result["execution_started"] is False
    assert result["submission_authorized"] is False
    assert result["human_review_required"] is True
    assert len(result["recommended_tasks"]) == 3
    assert all(
        task["execution_allowed"] is False
        for task in result["recommended_tasks"]
    )


def test_real_target_rejected(args):
    args["target"] = "example.com"
    with pytest.raises(ReconPlanningError):
        build_mission_advisory(**args)


def test_out_of_scope_rejected(args):
    args["target"] = "other.example"
    with pytest.raises(ReconPlanningError):
        build_mission_advisory(**args)


def test_unknown_authorization_rejected(args):
    args["authorization_id"] = "invalid"
    with pytest.raises(ValueError):
        build_mission_advisory(**args)


def test_missing_tool_blocks_dependents(args):
    args["tool_inventory"]["subfinder"] = {
        "executable_present": False
    }

    result = build_mission_advisory(**args)

    assert result["recommended_tasks"] == []
    assert len(result["blocked_tasks"]) == 3
    assert result["execution_authorized"] is False


def test_budget_enforced(args):
    args["budget"] = 1
    result = build_mission_advisory(**args)

    assert len(result["recommended_tasks"]) == 1
    assert result["planned_cost"] == 1
    assert result["automatic_execution_allowed"] is False
