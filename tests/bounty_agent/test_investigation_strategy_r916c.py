
"""R9.16C: offline investigation strategy tests."""

import pytest

from core.bounty_agent.autonomy.investigation_strategy import (
    StrategyError,
    build_strategy,
)


@pytest.fixture
def artifact():
    return {
        "simulation_only": True,
        "authorization_id": "auth-test",
        "recon_plan": {
            "target": "training.example",
            "authorization_id": "auth-test",
            "execution_started": False,
            "automatic_execution_allowed": False,
            "tasks": [],
        },
        "findings": [{
            "target": "training.example",
            "validated_vulnerability": False,
            "evidence": {
                "target": "training.example",
                "source": "mock_adapter",
                "status_code": 200,
            },
        }],
    }


def test_strategy_requires_human_review(artifact):
    result = build_strategy(artifact=artifact)

    assert result["recommended_next_action"] == "human_review"
    assert result["opportunities"][0]["priority_score"] == 0
    assert result["automatic_execution_allowed"] is False


def test_strategy_rejects_wrong_target(artifact):
    artifact["findings"][0]["target"] = "other.example"

    with pytest.raises(StrategyError):
        build_strategy(artifact=artifact)


def test_strategy_rejects_vulnerability_claim(artifact):
    artifact["findings"][0]["validated_vulnerability"] = True

    with pytest.raises(StrategyError):
        build_strategy(artifact=artifact)


def test_strategy_rejects_untrusted_evidence(artifact):
    artifact["findings"][0]["evidence"]["source"] = "unknown"

    with pytest.raises(StrategyError):
        build_strategy(artifact=artifact)


def test_strategy_rejects_execution_enabled(artifact):
    artifact["recon_plan"]["automatic_execution_allowed"] = True

    with pytest.raises(StrategyError):
        build_strategy(artifact=artifact)


def test_strategy_handles_empty_findings(artifact):
    artifact["findings"] = []

    result = build_strategy(artifact=artifact)

    assert result["opportunities"] == []
    assert result["recommended_next_action"] == "await_evidence"
