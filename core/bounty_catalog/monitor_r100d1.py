"""R10.0D1: one-shot, supervised HackerOne catalog monitoring.

Only the existing HackerOne program-metadata discovery command is invoked.
No recon, targets, mission creation, report submission or notifications.
This module does not install any scheduler. Default invocation is dry-run.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time
from typing import Any

from .operations_r100a import default_catalog, default_ledger, ingest

SCHEMA = "jarvis.bounty.monitor.r10d1"
MAX_PAGES = 20
REPO_ROOT = Path(__file__).resolve().parents[2]


class MonitorError(RuntimeError):
    """The monitor cannot proceed safely."""


class MonitorBusy(MonitorError):
    """Another monitor invocation owns the lock."""


def _private_directory() -> Path:
    directory = Path(default_ledger()).expanduser().parent
    if directory.is_symlink():
        raise MonitorError("Monitor directory is a symlink")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise MonitorError("Monitor directory must be owned with mode 0700")
    return directory


def _private_file(directory: Path, name: str, flags: int) -> int:
    path = directory / name
    descriptor = os.open(
        path,
        flags | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
    )
    info = os.fstat(descriptor)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
        or info.st_nlink != 1
    ):
        os.close(descriptor)
        raise MonitorError("Unsafe monitor state file")
    return descriptor


@contextmanager
def _monitor_lock():
    directory = _private_directory()
    fd = _private_file(directory, "r10d1.lock", os.O_RDWR)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MonitorBusy("Another monitor invocation is running") from exc
        yield directory
    finally:
        os.close(fd)


def _latest_run(path: Path) -> dict[str, str] | None:
    path = Path(path).expanduser()
    if path.is_symlink():
        raise MonitorError("Catalog symlink forbidden")
    if not path.exists():
        return None
    if not path.is_file():
        raise MonitorError("Catalog is not a regular file")
    try:
        with sqlite3.connect(
            path.resolve(strict=True).as_uri() + "?mode=ro",
            uri=True,
            timeout=10,
        ) as db:
            db.execute("PRAGMA query_only=ON")
            row = db.execute(
                "SELECT id, status FROM runs "
                "WHERE source=? ORDER BY rowid DESC LIMIT 1",
                ("hackerone-api",),
            ).fetchone()
    except sqlite3.Error as exc:
        raise MonitorError("Catalog metadata unreadable") from exc
    if row is None:
        return None
    if not all(isinstance(value, str) for value in row):
        raise MonitorError("Invalid catalog run metadata")
    return {"id": row[0], "status": row[1]}


def _write_receipt(directory: Path, record: dict[str, Any]) -> None:
    # Only bounded metadata is recorded. Never record subprocess output,
    # environment variables, stored tokens, API responses or credentials.
    permitted = (
        "status", "previous_run_id", "catalog_run_id", "discovery_exit_code",
        "ingestion_status", "new_events", "pending_review",
    )
    receipt = {"recorded_at": time.time(), "schema": SCHEMA}
    receipt.update({key: record[key] for key in permitted if key in record})
    line = (json.dumps(receipt, separators=(",", ":")) + "\n").encode()
    fd = _private_file(directory, "r10d1_runs.jsonl", os.O_WRONLY | os.O_APPEND)
    try:
        count = os.write(fd, line)
        if count != len(line):
            raise MonitorError("Incomplete monitor receipt")
        os.fsync(fd)
    finally:
        os.close(fd)


def _response(status: str, **fields: Any) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": status,
        "catalog_discovery_only": True,
        "testing_authorized": False,
        "execution_authorized": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
        **fields,
    }


def _check_ingestion(data: Any) -> None:
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("status"), str)
        or data.get("network_requests") != 0
        or data.get("testing_authorized") is not False
        or data.get("execution_authorized") is not False
        or data.get("notification_authorized") is not False
        or data.get("alerts_issued") != 0
        or type(data.get("new_events")) is not int
        or data["new_events"] < 0
        or type(data.get("pending_review")) is not int
        or data["pending_review"] < 0
    ):
        raise MonitorError("Operations ingestion safety contract failed")


def monitor_once(*, execute: bool = False, timeout_seconds: int = 900):
    """Run one metadata-only discovery and ingest a new *complete* snapshot.

    No timer, notifications or testing operations are started. Dry-run
    performs no I/O to the catalog or private monitor state.
    """
    if type(execute) is not bool:
        raise ValueError("execute must be a boolean")
    if type(timeout_seconds) is not int or not 60 <= timeout_seconds <= 1800:
        raise ValueError("Timeout must be an integer between 60 and 1800")

    if not execute:
        return _response(
            "dry_run", max_pages=MAX_PAGES,
            timeout_seconds=timeout_seconds,
            discovery_command=[
                sys.executable, "-m", "core.bounty_catalog", "discover",
                "--max-pages", str(MAX_PAGES),
            ],
            timer_enabled=False,
            state_modified=False,
        )

    try:
        with _monitor_lock() as directory:
            def finish(status: str, **fields: Any):
                output = _response(status, **fields)
                _write_receipt(directory, output)
                return output

            try:
                previous = _latest_run(default_catalog())
            except MonitorError:
                return finish("catalog_unavailable")

            previous_id = previous["id"] if previous else None
            command = [
                sys.executable, "-m", "core.bounty_catalog", "discover",
                "--max-pages", str(MAX_PAGES),
            ]
            try:
                outcome = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return finish("discovery_timeout", previous_run_id=previous_id)
            except OSError:
                return finish("discovery_unavailable", previous_run_id=previous_id)

            if outcome.returncode != 0:
                return finish(
                    "discovery_failed", previous_run_id=previous_id,
                    discovery_exit_code=outcome.returncode,
                )

            try:
                current = _latest_run(default_catalog())
            except MonitorError:
                return finish("catalog_unavailable", previous_run_id=previous_id)

            if current is None or current["id"] == previous_id:
                return finish("snapshot_not_advanced", previous_run_id=previous_id)

            if current["status"] != "complete":
                return finish(
                    "snapshot_incomplete", previous_run_id=previous_id,
                    catalog_run_id=current["id"],
                )

            try:
                data = ingest()
                _check_ingestion(data)
            except (Exception, KeyboardInterrupt):
                return finish(
                    "ingestion_failed", previous_run_id=previous_id,
                    catalog_run_id=current["id"],
                )

            return finish(
                "success", previous_run_id=previous_id,
                catalog_run_id=current["id"],
                ingestion_status=data["status"],
                new_events=data["new_events"],
                pending_review=data["pending_review"],
            )
    except MonitorBusy:
        return _response("already_running")
    except (MonitorError, OSError):
        return _response("monitor_unavailable")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R10.0D1 one-shot HackerOne metadata monitor (dry-run by default)"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Explicitly perform HackerOne metadata discovery and ledger ingestion",
    )
    parser.add_argument(
        "--timeout", type=int, default=900,
        help="Discovery subprocess timeout in seconds (60..1800)",
    )
    args = parser.parse_args()
    try:
        outcome = monitor_once(execute=args.run, timeout_seconds=args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(outcome, indent=2))
    return 0 if outcome["status"] in ("dry_run", "success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
