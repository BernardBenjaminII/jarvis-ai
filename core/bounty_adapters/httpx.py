"""Fixed single-host HTTPX metadata probe."""

from __future__ import annotations

import json
import time

from .base import binary, execute


CAPABILITY = "httpx"


def probe_http(scope, host, *, scheme="https", cancel=None):
    host = scope.require(host, CAPABILITY)

    if scheme not in {"http", "https"}:
        raise ValueError("Scheme must be http or https")

    exe = binary("httpx")

    target = f"{scheme}://{host}"

    # Fixed argument surface.
    #
    # Redirect following is deliberately not enabled. A redirect destination may
    # be outside the reviewed bounty scope and should require its own scope check.
    argv = [
        exe,
        "-silent",
        "-u",
        target,
        "-json",
        "-no-color",
    ]

    started = time.time()

    result = execute(
        argv,
        timeout=30,
        output_limit=262144,
        cancel=cancel,
    )

    records = []

    for line in (result.get("output") or "").splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            records.append(value)

    return {
        "adapter": CAPABILITY,
        "target": host,
        "scheme": scheme,
        "state": result.get("state"),
        "returncode": result.get("returncode"),
        "started_at": started,
        "finished_at": time.time(),
        "scope": scope.evidence(),
        "records": records,
        "raw_output_bytes": result.get("bytes", 0),
    }
