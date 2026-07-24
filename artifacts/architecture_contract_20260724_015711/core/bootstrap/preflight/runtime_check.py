from __future__ import annotations

import os
from pathlib import Path

from ..check import BootstrapCheck


class RuntimeMountCheck(BootstrapCheck):

    stage = "Preflight"
    name = "Runtime Storage"

    def execute(self):

        runtime = Path(
            os.environ.get(
                "JARVIS_RUNTIME",
                "/media/abdullah/JARVIS_RUNTIME_L",
            )
        )

        ok = runtime.exists()

        return ok, str(runtime)
