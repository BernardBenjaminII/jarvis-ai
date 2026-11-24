"""R10.0D1 isolated, network-free monitor regressions."""

import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess

import pytest

from core.bounty_catalog import monitor_r100d1 as monitor


def paths(tmp_path, monkeypatch):
    catalog = tmp_path / "bounty_catalog" / "r4.sqlite"
    ledger = tmp_path / "bounty_operations" / "r10_events.sqlite3"
    monkeypatch.setattr(monitor, "default_catalog", lambda: catalog)
    monkeypatch.setattr(monitor, "default_ledger", lambda: ledger)
    return catalog, ledger


def add_run(path, run_id, status="complete"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS runs "
            "(id TEXT, source TEXT, status TEXT)"
        )
        db.execute(
            "INSERT INTO runs VALUES (?, 'hackerone-api', ?)",
            (run_id, status),
        )


def safe_ingestion(events=2, pending=7):
    return {
        "status": "events_recorded",
        "new_events": events,
        "pending_review": pending,
        "network_requests": 0,
        "testing_authorized": False,
        "execution_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
    }


def test_default_is_dry_run_without_files_or_discovery(tmp_path, monkeypatch):
    catalog, ledger = paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        monitor.subprocess, "run",
        lambda *args, **kw: pytest.fail("Dry-run attempted discovery"),
    )
    result = monitor.monitor_once()
    assert result["status"] == "dry_run"
    assert result["state_modified"] is False
    assert result["alerts_issued"] == 0
    assert not catalog.exists()
    assert not ledger.parent.exists()


def test_complete_new_snapshot_ingests_once_and_logs_safely(tmp_path, monkeypatch):
    catalog, ledger = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")
    invoked = []

    def discover(command, **kwargs):
        assert command[-2:] == ["--max-pages", "20"]
        assert kwargs["timeout"] == 900
        assert kwargs["stdin"] == subprocess.DEVNULL
        invoked.append("discover")
        add_run(catalog, "new-run")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(monitor.subprocess, "run", discover)
    monkeypatch.setattr(
        monitor, "ingest", lambda: invoked.append("ingest") or safe_ingestion()
    )
    result = monitor.monitor_once(execute=True)
    assert result["status"] == "success"
    assert result["previous_run_id"] == "baseline"
    assert result["catalog_run_id"] == "new-run"
    assert result["new_events"] == 2
    assert invoked == ["discover", "ingest"]
    directory = ledger.parent
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for name in ("r10d1.lock", "r10d1_runs.jsonl"):
        assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600
    records = (directory / "r10d1_runs.jsonl").read_text().splitlines()
    assert len(records) == 1
    assert json.loads(records[0])["status"] == "success"
    assert "secret" not in records[0]


def test_incomplete_snapshot_skips_ingestion(tmp_path, monkeypatch):
    catalog, _ = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")

    def discover(command, **kwargs):
        add_run(catalog, "limited-run", "limited")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(monitor.subprocess, "run", discover)
    monkeypatch.setattr(
        monitor, "ingest", lambda: pytest.fail("Ingested incomplete snapshot")
    )
    result = monitor.monitor_once(execute=True)
    assert result["status"] == "snapshot_incomplete"
    assert result["alerts_issued"] == 0


def test_no_new_snapshot_skips_ingestion(tmp_path, monkeypatch):
    catalog, _ = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")
    monkeypatch.setattr(
        monitor.subprocess, "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0),
    )
    monkeypatch.setattr(
        monitor, "ingest", lambda: pytest.fail("Ingested duplicate snapshot")
    )
    assert monitor.monitor_once(execute=True)["status"] == "snapshot_not_advanced"


def test_discovery_error_does_not_ingest(tmp_path, monkeypatch):
    catalog, _ = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")
    monkeypatch.setattr(
        monitor.subprocess, "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 23),
    )
    monkeypatch.setattr(
        monitor, "ingest", lambda: pytest.fail("Ingested failed discovery")
    )
    result = monitor.monitor_once(execute=True)
    assert result["status"] == "discovery_failed"
    assert result["discovery_exit_code"] == 23


def test_timeout_does_not_ingest(tmp_path, monkeypatch):
    catalog, _ = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")

    def timeout(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])

    monkeypatch.setattr(monitor.subprocess, "run", timeout)
    monkeypatch.setattr(
        monitor, "ingest", lambda: pytest.fail("Ingested timed-out discovery")
    )
    assert monitor.monitor_once(execute=True)["status"] == "discovery_timeout"


def test_existing_monitor_lock_blocks_duplicate_run(tmp_path, monkeypatch):
    paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        monitor.subprocess, "run",
        lambda *a, **k: pytest.fail("Ran during lock contention"),
    )
    with monitor._monitor_lock():
        result = monitor.monitor_once(execute=True)
    assert result["status"] == "already_running"


def test_unsafe_ingestion_contract_fails_closed(tmp_path, monkeypatch):
    catalog, _ = paths(tmp_path, monkeypatch)
    add_run(catalog, "baseline")

    def discover(cmd, **kwargs):
        add_run(catalog, "new-run")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(monitor.subprocess, "run", discover)
    monkeypatch.setattr(
        monitor, "ingest",
        lambda: {**safe_ingestion(), "execution_authorized": True},
    )
    result = monitor.monitor_once(execute=True)
    assert result["status"] == "ingestion_failed"
    assert result["notification_authorized"] is False
    assert result["alerts_issued"] == 0


def test_invalid_timeout_rejected(tmp_path, monkeypatch):
    paths(tmp_path, monkeypatch)
    for value in (0, 30, 1801, True, "900"):
        with pytest.raises(ValueError):
            monitor.monitor_once(execute=True, timeout_seconds=value)
