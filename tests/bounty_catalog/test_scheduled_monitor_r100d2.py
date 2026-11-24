"""Offline R10.0D2 scheduler safety and notifications tests."""

import subprocess

import pytest

from core.bounty_catalog import scheduled_monitor_r100d2 as m


def receipt(new=0, **overrides):
    data = {
        "schema": "jarvis.bounty.monitor.r10d1",
        "status": "success",
        "catalog_discovery_only": True,
        "testing_authorized": False,
        "execution_authorized": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
        "catalog_run_id": "synthetic-run-123",
        "ingestion_status": "ingested",
        "new_events": new,
        "pending_review": 7 + new,
    }
    data.update(overrides)
    return data


def test_dry_run_does_not_invoke_monitor(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: pytest.fail("monitor called"))
    result = m.scheduled_once()
    assert result["status"] == "dry_run"
    assert result["state_modified"] is False
    assert result["notification_status"] == "not_attempted"


def test_zero_events_never_notifies(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: receipt())
    monkeypatch.setattr(m, "_notify_new_events", lambda _: pytest.fail("notified"))
    result = m.scheduled_once(execute=True)
    assert result["new_events"] == 0
    assert result["notification_status"] == "not_needed"


def test_positive_events_notify_once(monkeypatch):
    calls = []
    monkeypatch.setattr(m, "monitor_once", lambda **_: receipt(3))
    monkeypatch.setattr(m, "_notify_new_events", lambda count: (calls.append(count), "sent")[1])
    result = m.scheduled_once(execute=True)
    assert result["notification_status"] == "sent"
    assert calls == [3]


def test_no_notify_option_skips_notification(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: receipt(4))
    monkeypatch.setattr(m, "_notify_new_events", lambda _: pytest.fail("notified"))
    assert m.scheduled_once(execute=True, notify=False)["notification_status"] == "not_requested"


def test_monitor_failure_cannot_notify(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: {"status": "snapshot_incomplete"})
    monkeypatch.setattr(m, "_notify_new_events", lambda _: pytest.fail("notified"))
    result = m.scheduled_once(execute=True)
    assert result["status"] == "monitor_failed"


@pytest.mark.parametrize("change", [
    {"testing_authorized": True},
    {"execution_authorized": True},
    {"submission_authorized": True},
    {"notification_authorized": True},
    {"alerts_issued": 1},
    {"new_events": True},
    {"new_events": -1},
    {"ingestion_status": "unknown"},
    {"catalog_run_id": ""},
    {"schema": "wrong"},
])
def test_bad_contract_fails_closed(monkeypatch, change):
    monkeypatch.setattr(m, "monitor_once", lambda **_: receipt(1, **change))
    monkeypatch.setattr(m, "_notify_new_events", lambda _: pytest.fail("notified"))
    with pytest.raises(m.SchedulerError):
        m.scheduled_once(execute=True)


def test_notification_has_no_program_names_or_tokens(monkeypatch):
    calls = []
    monkeypatch.setattr(m.shutil, "which", lambda _: "/usr/bin/notify-send")
    monkeypatch.setenv("DISPLAY", ":0.0")
    monkeypatch.setattr(m.subprocess, "run", lambda command, **kwargs: (calls.append(command), subprocess.CompletedProcess(command, 0))[1])
    assert m._notify_new_events(2) == "sent"
    assert len(calls) == 1
    assert "2 new catalog change" in " ".join(calls[0])
    assert all("secret" not in part.lower() for part in calls[0])


def test_no_graphical_session_is_nonfatal(monkeypatch):
    monkeypatch.setattr(m.shutil, "which", lambda _: "/usr/bin/notify-send")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert m._notify_new_events(2) == "no_graphical_session"


def test_notification_failure_is_nonfatal(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: receipt(2))
    monkeypatch.setattr(m, "_notify_new_events", lambda _: "failed")
    result = m.scheduled_once(execute=True)
    assert result["status"] == "success"
    assert result["notification_status"] == "failed"


def test_invalid_timeout_fails_before_monitor(monkeypatch):
    monkeypatch.setattr(m, "monitor_once", lambda **_: pytest.fail("monitor called"))
    with pytest.raises(ValueError):
        m.scheduled_once(execute=True, timeout_seconds=0)
