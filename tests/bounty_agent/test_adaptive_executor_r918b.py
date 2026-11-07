import json

import pytest

from core.bounty_agent.autonomy import adaptive_executor_r918 as executor


def test_unapproved_mission_rejected(tmp_path):
    with pytest.raises(executor.ExecutionBoundaryError):
        executor.run_mission(
            mission=executor.LocalMission(approved=False),
            evidence_dir=tmp_path,
        )


def test_external_target_rejected(tmp_path):
    with pytest.raises(executor.ExecutionBoundaryError):
        executor.run_mission(
            mission=executor.LocalMission(
                approved=True,
                target="https://example.com/",
            ),
            evidence_dir=tmp_path,
        )


@pytest.mark.parametrize("budget", [0, 6, -1, True])
def test_invalid_budget_rejected(tmp_path, budget):
    with pytest.raises(executor.ExecutionBoundaryError):
        executor.run_mission(
            mission=executor.LocalMission(
                approved=True,
                max_requests=budget,
            ),
            evidence_dir=tmp_path,
        )


def test_unknown_capability_rejected():
    with pytest.raises(executor.ExecutionBoundaryError):
        executor.execute_capability("arbitrary_request")


def test_bounded_autonomous_execution(monkeypatch, tmp_path):
    executed = []

    def fake_execute(capability):
        executed.append(capability)
        return {
            "capability": capability,
            "probe": capability,
            "http_status": 200,
            "body_sha256": "a" * 64,
            "query_sha256": "b" * 64,
            "product_ids": [1, 2],
            "product_count": 2,
            "valid_product_response": True,
            "sqlite_error": None,
        }

    monkeypatch.setattr(
        executor, "execute_capability", fake_execute
    )

    result = executor.run_mission(
        mission=executor.LocalMission(
            approved=True,
            max_requests=5,
        ),
        evidence_dir=tmp_path,
    )

    assert len(executed) <= 5
    assert len(executed) == len(set(executed))
    assert executed[0] == "baseline_http"

    report = json.loads(
        open(result["evidence_path"], encoding="utf-8").read()
    )

    assert report["submission_authorized"] is False
    assert report["validated_vulnerability"] is False
    assert report["request_count"] == len(executed)


def test_failed_execution_preserves_evidence(monkeypatch, tmp_path):
    def fail(_capability):
        raise executor.ExecutionBoundaryError(
            "Simulated connection failure"
        )

    monkeypatch.setattr(
        executor, "execute_capability", fail
    )

    result = executor.run_mission(
        mission=executor.LocalMission(approved=True),
        evidence_dir=tmp_path,
    )

    assert result["stop_reason"] == "execution_boundary_failure"
    assert result["request_count"] == 1
    assert result["observations"][0]["state"] == "failed"
