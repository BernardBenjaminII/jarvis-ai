import hashlib
import json

import pytest

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG, LocalMission,
)
from core.bounty_agent.autonomy.adaptive_integration_r918c3 import (
    IntegratedResult, run_integrated,
)
from core.bounty_agent.autonomy.integration_evidence_r918c3 import (
    EvidenceError, persist,
)


def fake_runner(capability):
    query = CATALOG[capability][1]

    result = {
        "capability": capability,
        "query_sha256": hashlib.sha256(
            query.encode("utf-8")
        ).hexdigest(),
        "http_status": 200,
        "valid_product_response": True,
        "product_ids": [1, 2, 3],
        "sqlite_error": None,
    }

    if capability == "sql_syntax_diagnostic":
        result.update({
            "http_status": 500,
            "valid_product_response": False,
            "product_ids": [],
            "sqlite_error": "SQLite error observed",
        })

    return result


def test_persist_reproduced_diagnostic(tmp_path):
    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=fake_runner,
    )

    saved = persist(
        result=result,
        evidence_dir=tmp_path,
    )

    path = tmp_path / saved["evidence_path"].split("/")[-1]
    report = json.loads(path.read_text())

    assert saved["syntax_condition_reproduced"] is True
    assert saved["validated_vulnerability"] is False
    assert report["assessment"]["human_review_required"] is True
    assert report["assessment"]["submission_authorized"] is False
    assert len(report["observations"]) <= 5

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == saved["sha256"]


def test_evidence_not_overwritten(tmp_path):
    result = IntegratedResult(
        observations=(),
        stop_reason="no_experiments",
        request_count=0,
    )

    first = persist(result=result, evidence_dir=tmp_path)
    assert first["request_count"] == 0
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_invalid_count_rejected(tmp_path):
    result = IntegratedResult(
        observations=(),
        stop_reason="invalid",
        request_count=6,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_symlink_directory_rejected(tmp_path):
    destination = tmp_path / "real"
    destination.mkdir()

    link = tmp_path / "link"
    link.symlink_to(destination, target_is_directory=True)

    result = IntegratedResult(
        observations=(),
        stop_reason="no_experiments",
        request_count=0,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=link)


def test_unsafe_assessment_rejected(tmp_path):
    result = IntegratedResult(
        observations=(),
        stop_reason="invalid",
        request_count=0,
        validated_vulnerability=True,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_fabricated_query_hash_rejected(tmp_path):
    result = IntegratedResult(
        observations=({
            "capability": "baseline_http",
            "experiment_identity": "baseline_apple",
            "state": "completed",
            "query_sha256": "0" * 64,
        },),
        stop_reason="test",
        request_count=1,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_duplicate_experiment_rejected(tmp_path):
    entry = {
        "capability": "baseline_http",
        "experiment_identity": "baseline_apple",
        "state": "attempted",
    }

    result = IntegratedResult(
        observations=(entry, entry),
        stop_reason="test",
        request_count=2,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_unapproved_experiment_rejected(tmp_path):
    result = IntegratedResult(
        observations=({
            "capability": "arbitrary_network_scan",
            "experiment_identity": "unknown",
            "state": "attempted",
        },),
        stop_reason="test",
        request_count=1,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_reproduction_claim_must_match_evidence(tmp_path):
    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=fake_runner,
    )

    observations = [
        dict(item) for item in result.observations
    ]

    repeat = next(
        item for item in observations
        if item["capability"] == "syntax_repetition"
    )
    repeat["reproduces_syntax_error"] = False

    forged = IntegratedResult(
        observations=tuple(observations),
        stop_reason=result.stop_reason,
        request_count=len(observations),
    )

    with pytest.raises(EvidenceError):
        persist(result=forged, evidence_dir=tmp_path)


def test_failed_attempt_requires_category(tmp_path):
    result = IntegratedResult(
        observations=({
            "capability": "baseline_http",
            "experiment_identity": "baseline_apple",
            "state": "failed",
        },),
        stop_reason="execution_or_evidence_failure",
        request_count=1,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)


def test_unresolved_attempt_rejected(tmp_path):
    result = IntegratedResult(
        observations=({
            "capability": "baseline_http",
            "experiment_identity": "baseline_apple",
            "state": "attempted",
        },),
        stop_reason="unknown",
        request_count=1,
    )

    with pytest.raises(EvidenceError):
        persist(result=result, evidence_dir=tmp_path)
