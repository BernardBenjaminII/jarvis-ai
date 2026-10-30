"""Fixed single-host DNSX resolution adapter."""

from __future__ import annotations

import json
import time

from .base import binary, execute


CAPABILITY = "dnsx"


def resolve_dns(scope, host, *, cancel=None):
    """
    Resolve one already-reviewed hostname.

    The caller cannot supply command-line switches. The target
    must pass the reviewed provider/host scope before dnsx runs.
    """
    host = scope.require(
        host,
        CAPABILITY,
    )

    exe = binary("dnsx")

    # R9.1.1 fixed single-host argument surface.
    #
    # dnsx -d is domain/bruteforce mode and requires a
    # wordlist. A reviewed individual hostname must instead
    # be supplied through stdin.
    #
    # -a limits this adapter revision to A-record resolution.
    # -json gives structured evidence for later stages.
    argv = [
        exe,
        "-silent",
        "-a",
        "-json",
    ]

    started = time.time()

    result = execute(
        argv,
        timeout=30,
        output_limit=262144,
        cancel=cancel,
        stdin_text=host + "\n",
    )

    records = []
    candidates = []

    for line in (
        result.get("output") or ""
    ).splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(value, dict):
            continue

        records.append(value)

        candidate = (
            value.get("host")
            or value.get("input")
            or value.get("name")
        )

        if candidate:
            candidates.append(
                str(candidate)
            )

    # Some dnsx versions/outputs may omit the hostname in a
    # successful single-target structured record. The reviewed
    # input is the only permissible fallback.
    if records and not candidates:
        candidates.append(host)

    filtered = scope.filter_hosts(
        candidates
    )

    return {
        "adapter": CAPABILITY,
        "target": host,
        "query_type": "A",
        "state": result.get("state"),
        "returncode": result.get(
            "returncode"
        ),
        "started_at": started,
        "finished_at": time.time(),
        "scope": scope.evidence(),
        "records": records,
        "accepted": filtered["accepted"],
        "rejected": filtered["rejected"],
        "raw_output_bytes": result.get(
            "bytes",
            0,
        ),
    }
