"""Fixed passive subfinder adapter."""

from __future__ import annotations

import time

from .base import binary, execute


CAPABILITY = "subfinder"


def enumerate_subdomains(scope, domain, *, cancel=None):
    domain = scope.require(domain, CAPABILITY)

    exe = binary("subfinder")

    # Fixed argument surface. No caller-supplied switches.
    argv = [
        exe,
        "-silent",
        "-d",
        domain,
    ]

    started = time.time()

    result = execute(
        argv,
        timeout=30,
        output_limit=1048576,
        cancel=cancel,
    )

    discovered = []

    if result.get("output"):
        discovered = [
            line.strip()
            for line in result["output"].splitlines()
            if line.strip()
        ]

    filtered = scope.filter_hosts(discovered)

    return {
        "adapter": CAPABILITY,
        "target": domain,
        "state": result.get("state"),
        "returncode": result.get("returncode"),
        "started_at": started,
        "finished_at": time.time(),
        "scope": scope.evidence(),
        "accepted": filtered["accepted"],
        "rejected": filtered["rejected"],
        "raw_output_bytes": result.get("bytes", 0),
    }
