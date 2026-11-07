import json

from core.bounty_agent.report_export import (
    export_json,
    export_markdown,
)


def fixture_report():
    return {
        "session": {
            "id": "session-demo",
            "authorization": "auth-demo",
            "program": "Synthetic program",
            "root_target": "example.com",
            "state": "recon_complete",
            "updated": 1700000000,
        },
        "mission": {
            "mission": {
                "state": "ready",
                "budget": 5,
                "used": 1,
            },
            "tasks": [
                {
                    "id": "task-demo",
                    "capability": "subfinder",
                    "target": "example.com",
                    "state": "completed",
                    "evidence_sha256": "a" * 64,
                },
            ],
            "events": [],
            "proposals": [],
        },
        "options": [],
        "investigation_plans": [],
        "events": [],
    }


def test_r912_json_export_preserves_source():
    report = fixture_report()
    document = json.loads(export_json(report))

    assert document["source"] == report
    assert document["submission_status"] == "not_submitted"
    assert document["vulnerability_confirmation"] == (
        "not_asserted"
    )


def test_r912_markdown_preserves_evidence_reference():
    text = export_markdown(fixture_report())

    assert "task-demo" in text
    assert "a" * 64 in text
    assert "human review required" in text
    assert "Not submitted" in text
    assert "not independently confirmed" in text


def test_r912_markdown_escapes_untrusted_text():
    report = fixture_report()
    report["session"]["root_target"] = (
        "<script>alert(1)</script>\n# Forged heading"
    )

    text = export_markdown(report)

    assert "<script>" not in text
    assert "\n# Forged heading" not in text
    assert "&lt;script&gt;" in text


def test_r912_rejects_invalid_report():
    import pytest

    with pytest.raises(ValueError):
        export_json({"session": {}})
