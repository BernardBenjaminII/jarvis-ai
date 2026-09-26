"""Fixed-command bounty execution helpers.

Never expose command argv construction from this package to a language model,
HTTP request parameter, generic command dispatcher, or unreviewed mission data.
"""

from __future__ import annotations

import os
import shutil

from core.bounty_worker.runner import run_bounded


class AdapterUnavailable(RuntimeError):
    pass


_ALLOWED = {
    "subfinder",
    "httpx",
}


def binary(name: str) -> str:
    if name not in _ALLOWED:
        raise AdapterUnavailable("Unsupported adapter executable")

    path = shutil.which(name)

    if not path:
        raise AdapterUnavailable(f"{name} executable not found")

    path = os.path.realpath(path)

    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        raise AdapterUnavailable(f"{name} is not executable")

    return path


def execute(argv, *, timeout=30, output_limit=1048576, cancel=None):
    return run_bounded(
        argv,
        timeout=timeout,
        output_limit=output_limit,
        cancel=cancel,
    )
