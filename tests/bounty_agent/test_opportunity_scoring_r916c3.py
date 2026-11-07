
"""R9.16C.3: opportunity scoring regression tests."""

import copy

import pytest

from core.bounty_agent.autonomy.opportunity_scoring import (
    ScoringError,
    score_opportunities,
)


def opportunity(value, effort, capability="http_probe"):
    return {
        "target": "training.example",
        "simulation_only": True,
        "validated_vulnerability": False,
        "evidence": {
            "source": "mock_adapter",
            "target": "training.example",
            "observation": f"synthetic-{value}-{effort}",
        },
        "evidence_quality": 3,
        "investigation_value": value,
        "estimated_effort": effort,
        "required_capability": capability,
    }


def evaluate(items, budget=5, capabilities=None):
    return score_opportunities(
        opportunities=items,
        authorized_target="training.example",
        available_capabilities=(
            ["http_probe", "dns_resolution"]
            if capabilities is None
            else capabilities
        ),
        budget=budget,
    )


def test_higher_value_opportunity_ranks_first():
    result = evaluate([
        opportunity(2, 2),
        opportunity(5, 2),
    ])

    assert result["recommended"]["priority_score"] == 23
    assert result["recommended"]["estimated_effort"] == 2


def test_missing_capability_blocks_opportunity():
    result = evaluate([
        opportunity(5, 1, "manual_web_testing")
    ])

    assert result["recommended"] is None
    assert result["ranked_opportunities"][0]["blockers"] == [
        "capability_unavailable"
    ]


def test_budget_blocks_expensive_opportunity():
    result = evaluate([opportunity(5, 5)], budget=2)

    assert result["recommended"] is None
    assert "insufficient_budget" in (
        result["ranked_opportunities"][0]["blockers"]
    )


def test_out_of_scope_target_rejected():
    item = opportunity(3, 2)
    item["target"] = "other.example"

    with pytest.raises(ScoringError):
        evaluate([item])


def test_untrusted_evidence_rejected():
    item = opportunity(3, 2)
    item["evidence"]["source"] = "external"

    with pytest.raises(ScoringError):
        evaluate([item])


def test_vulnerability_claim_rejected():
    item = opportunity(3, 2)
    item["validated_vulnerability"] = True

    with pytest.raises(ScoringError):
        evaluate([item])


def test_deterministic_ranking():
    items = [
        opportunity(2, 3),
        opportunity(5, 1),
        opportunity(3, 2),
    ]

    first = evaluate(copy.deepcopy(items))
    second = evaluate(list(reversed(copy.deepcopy(items))))

    assert first["ranked_opportunities"] == (
        second["ranked_opportunities"]
    )


def test_empty_opportunities():
    result = evaluate([])

    assert result["recommended"] is None
    assert result["ranked_opportunities"] == []


def test_invalid_budget_rejected():
    with pytest.raises(ScoringError):
        evaluate([opportunity(3, 1)], budget=0)


def test_execution_remains_disabled():
    result = evaluate([opportunity(5, 1)])

    assert result["automatic_execution_allowed"] is False
    assert result["vulnerability_validation_allowed"] is False
    assert result["report_submission_allowed"] is False
    assert result["recommended"]["execution_allowed"] is False
    assert result["recommended"]["vulnerability_confidence"] == 0
