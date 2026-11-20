"""R9.22C2A restriction-aware capability regression."""

import copy

import pytest

from core.capabilities.kali_workstation import TOOLS
from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_policy_capability_r922c2 import (
    assess_program_capabilities,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)


def draft():
    return create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["admin.training.example"],
        restrictions=["No automated scanning"],
    )


def inventory():
    return {
        "state": "ready",
        "mode": "inventory_only",
        "execution_authorized": False,
        "tool_count": len(TOOLS),
        "installed_count": len(TOOLS),
        "tools": {
            name: {"installed": True, "path": f"/usr/bin/{name}"}
            for name in TOOLS
        },
    }


def test_unknown_permission_remains_unknown():
    result = assess_program_capabilities(draft(), inventory())

    assert all(
        item["policy_status"] == "permission_unknown"
        for item in result["categories"].values()
    )
    assert result["mission_creation_allowed"] is False
    assert result["testing_authorized"] is False


def test_explicitly_classified_restriction():
    result = assess_program_capabilities(
        draft(),
        inventory(),
        restriction_evidence={
            "template_analysis": "No automated scanning"
        },
    )

    assert (
        result["categories"]["template_analysis"]["policy_status"]
        == "operator_flagged_restriction_unverified"
    )
    assert (
        result["categories"]["dns_resolution"]["policy_status"]
        == "permission_unknown"
    )
    assert result["execution_enabled"] is False


def test_unrecorded_restriction_rejected():
    with pytest.raises(OpportunityQueueError):
        assess_program_capabilities(
            draft(),
            inventory(),
            restriction_evidence={
                "http_observation": "All scanning permitted"
            },
        )


def test_unknown_category_rejected():
    with pytest.raises(OpportunityQueueError):
        assess_program_capabilities(
            draft(),
            inventory(),
            restriction_evidence={
                "unknown_tool": "No automated scanning"
            },
        )


def test_forged_execution_authorization_rejected():
    forged = draft()
    forged["execution_authorized"] = True

    with pytest.raises(ValueError):
        assess_program_capabilities(forged, inventory())


def test_tampered_policy_rejected():
    forged = copy.deepcopy(draft())
    forged["restrictions"] = ["All scanning permitted"]

    with pytest.raises(ValueError):
        assess_program_capabilities(forged, inventory())


def test_workstation_permission_cannot_be_forged():
    forged = inventory()
    forged["execution_authorized"] = True

    with pytest.raises(ValueError):
        assess_program_capabilities(draft(), forged)
