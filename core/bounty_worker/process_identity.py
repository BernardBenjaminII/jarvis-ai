"""Linux process identity for JARVIS worker recovery.

Identity is PID + boot ID + kernel start ticks.
This verifies process identity, not its child-process tree.
"""

from __future__ import annotations

import os
from pathlib import Path


def process_identity(pid: int) -> dict | None:
    """Return the identity of a visible Linux process."""
    if type(pid) is not int or pid <= 0:
        raise ValueError("PID must be a positive integer")

    try:
        boot_id = Path(
            "/proc/sys/kernel/random/boot_id"
        ).read_text().strip()

        stat = Path(f"/proc/{pid}/stat").read_text()
        # The process name is parenthesized and may
        # contain spaces or closing parentheses.
        closing = stat.rfind(")")
        if closing < 0:
            return None

        fields = stat[closing + 2:].split()
        # Fields after comm start with field 3.
        # Kernel field 22 is starttime.
        start_ticks = int(fields[19])

        return {
            "pid": pid,
            "boot_id": boot_id,
            "start_ticks": start_ticks,
        }
    except (FileNotFoundError, ProcessLookupError):
        return None
    except (PermissionError, OSError, ValueError, IndexError):
        return None


def identity_status(identity: dict) -> str:
    """Return same_process, absent_or_replaced, or unknown."""
    if not isinstance(identity, dict):
        return "unknown"

    pid = identity.get("pid")
    boot = identity.get("boot_id")
    ticks = identity.get("start_ticks")

    if (
        type(pid) is not int or pid <= 0
        or not isinstance(boot, str) or not boot
        or type(ticks) is not int or ticks < 0
    ):
        return "unknown"

    try:
        current_boot = Path(
            "/proc/sys/kernel/random/boot_id"
        ).read_text().strip()
    except OSError:
        return "unknown"

    if current_boot != boot:
        return "absent_or_replaced"

    current = process_identity(pid)
    if current is None:
        # A missing /proc entry normally indicates exit,
        # but inaccessible process data is indistinguishable.
        return "unknown"

    if current == identity:
        return "same_process"

    return "absent_or_replaced"


def current_identity() -> dict | None:
    return process_identity(os.getpid())
