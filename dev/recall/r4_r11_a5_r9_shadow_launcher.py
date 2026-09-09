"""
Genesis Recall R4-R11-A5-R9-R1
Diagnostic-only shadow ASGI launcher.

This file is NOT production runtime code.
"""

from __future__ import annotations

import runpy

_runtime = runpy.run_path(
    "/tmp/genesis_recall_r4_r11_a5_r9_runtime.py"
)

if "app" not in _runtime:
    raise RuntimeError(
        "R9 runtime tracer completed without exporting FastAPI 'app'"
    )

app = _runtime["app"]
