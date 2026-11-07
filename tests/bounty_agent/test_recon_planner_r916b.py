
"""R9.16B: offline reconnaissance planner tests."""

import pytest

from core.bounty_agent.autonomy.recon_planner import (
    ReconPlanningError,
    build_recon_plan,
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
            raise ValueError("Out of scope")


class Store:
    def live_scope(self, authorization_id):
        if authorization_id != "auth-test":
            raise ValueError("Unknown authorization")
        return Scope()


@pytest.fixture
def arguments():
    return {
        "authorization_store": Store(),
        "authorization_id": "auth-test",
        "program": "training",
        "target": "training.example",
        "budget": 2,
        "tool_inventory": {
            "subfinder": {"executable_present": True},
            "dnsx": {"executable_present": True},
            "httpx": {"recon_available": True},
        },
    }


def test_planner_respects_budget(arguments):
    plan = build_recon_plan(**arguments)

    assert len(plan["tasks"]) == 2
    assert plan["planned_cost"] == 2
    assert plan["execution_started"] is False
    assert plan["automatic_execution_allowed"] is False
    assert plan["blocked"][-1]["reason"] == "budget_exhausted"


def test_planner_rejects_out_of_scope(arguments):
    arguments["target"] = "other.example"

    with pytest.raises(ReconPlanningError):
        build_recon_plan(**arguments)


def test_planner_rejects_non_synthetic_target(arguments):
    arguments["target"] = "example.com"

    with pytest.raises(ReconPlanningError):
        build_recon_plan(**arguments)


def test_planner_blocks_missing_tools(arguments):
    arguments["tool_inventory"] = {}

    plan = build_recon_plan(**arguments)

    assert plan["tasks"] == []
    assert len(plan["blocked"]) == 3


def test_planner_rejects_invalid_budget(arguments):
    arguments["budget"] = 0

    with pytest.raises(ReconPlanningError):
        build_recon_plan(**arguments)


def test_missing_dependency_blocks_downstream(arguments):
    arguments["tool_inventory"]["subfinder"] = {
        "executable_present": False
    }

    plan = build_recon_plan(**arguments)

    assert plan["tasks"] == []

    reasons = {
        item["capability"]: item["reason"]
        for item in plan["blocked"]
    }

    assert reasons["subdomain_discovery"] == (
        "tool_not_installed"
    )
    assert reasons["dns_resolution"] == (
        "dependency_unavailable"
    )
    assert reasons["http_probe"] == (
        "dependency_unavailable"
    )
