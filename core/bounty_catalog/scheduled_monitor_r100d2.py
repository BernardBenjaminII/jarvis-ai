"""R10.0D2 scheduled, metadata-only catalog monitor with optional desktop notice.

Schedule is controlled by a separately installed systemd user timer.
Never executes target recon, missions, vulnerability tests, or submissions.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from .monitor_r100d1 import monitor_once

SCHEMA = "jarvis.bounty.scheduled_monitor.r10d2"


class SchedulerError(ValueError):
    pass


def _validate_monitor(result):
    """Fail closed before sending any notification."""
    if not isinstance(result, dict):
        raise SchedulerError("Monitor returned invalid data")
    if result.get("status") != "success":
        return False
    if (
        result.get("schema") != "jarvis.bounty.monitor.r10d1"
        or result.get("catalog_discovery_only") is not True
        or result.get("testing_authorized") is not False
        or result.get("execution_authorized") is not False
        or result.get("mission_creation_allowed") is not False
        or result.get("submission_authorized") is not False
        or result.get("notification_authorized") is not False
        or result.get("alerts_issued") != 0
        or result.get("ingestion_status") not in ("ingested", "up_to_date")
        or not isinstance(result.get("catalog_run_id"), str)
        or not result["catalog_run_id"]
        or type(result.get("new_events")) is not int
        or result["new_events"] < 0
        or type(result.get("pending_review")) is not int
        or result["pending_review"] < 0
    ):
        raise SchedulerError("Monitor safety contract failed")
    return True


def _notify_new_events(count):
    """Best-effort local notification; never sends program or credential data."""
    if type(count) is not int or count <= 0:
        return "not_needed"
    executable = shutil.which("notify-send")
    if not executable:
        return "unavailable"
    # A user service can run without any graphical session. Never invent one.
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return "no_graphical_session"
    try:
        done = subprocess.run(
            [
                executable,
                "--app-name=JARVIS",
                "--urgency=normal",
                "--expire-time=12000",
                "JARVIS Bounty Review",
                f"{count} new catalog change(s) require human review. "
                "Open the Opportunity Review Queue in Mission Control.",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "failed"
    return "sent" if done.returncode == 0 else "failed"


def scheduled_once(*, execute=False, notify=True, timeout_seconds=900):
    """One-shot entrypoint; dry-run unless --run is explicitly supplied."""
    if type(execute) is not bool or type(notify) is not bool:
        raise ValueError("Invalid monitor flags")
    if type(timeout_seconds) is not int or not 60 <= timeout_seconds <= 1800:
        raise ValueError("Invalid timeout")

    base = {
        "schema": SCHEMA,
        "catalog_discovery_only": True,
        "testing_authorized": False,
        "execution_authorized": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
        "notifications_are_local_only": True,
    }
    if not execute:
        return {
            **base,
            "status": "dry_run",
            "new_events": 0,
            "notification_status": "not_attempted",
            "timer_enabled": False,
            "state_modified": False,
        }

    result = monitor_once(execute=True, timeout_seconds=timeout_seconds)
    if not _validate_monitor(result):
        return {
            **base,
            "status": "monitor_failed",
            "monitor_status": str(result.get("status", "unknown"))[:80],
            "new_events": 0,
            "notification_status": "not_attempted",
        }

    count = result["new_events"]
    notice = (
        _notify_new_events(count)
        if notify and count > 0
        else ("not_requested" if not notify else "not_needed")
    )
    return {
        **base,
        "status": "success",
        "catalog_run_id": result["catalog_run_id"],
        "ingestion_status": result["ingestion_status"],
        "new_events": count,
        "pending_review": result["pending_review"],
        "notification_status": notice,
    }


def main():
    parser = argparse.ArgumentParser(
        description="R10.0D2 scheduled catalog metadata monitor (dry-run by default)"
    )
    parser.add_argument("--run", action="store_true", help="Execute one discovery/ingestion")
    parser.add_argument("--no-notify", action="store_true", help="Skip desktop notification")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    try:
        result = scheduled_once(
            execute=args.run,
            notify=not args.no_notify,
            timeout_seconds=args.timeout,
        )
    except (SchedulerError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("dry_run", "success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
