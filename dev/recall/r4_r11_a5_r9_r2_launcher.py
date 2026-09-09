from __future__ import annotations

import runpy

runtime = runpy.run_path(
    "/tmp/genesis_recall_r4_r11_a5_r9_r2_runtime.py"
)

if "app" not in runtime:
    raise RuntimeError(
        "R9-R2 runtime did not export FastAPI app"
    )

app = runtime["app"]
