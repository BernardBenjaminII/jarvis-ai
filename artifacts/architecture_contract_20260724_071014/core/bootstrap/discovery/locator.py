from __future__ import annotations

import json
import os
from pathlib import Path


class RuntimeLocator:

    def __init__(self, environment: str):
        self.environment = environment

    def locate(self):

        env_override = os.environ.get("JARVIS_RUNTIME")

        if env_override:
            return Path(env_override)

        username = (
            os.environ.get("USER")
            or os.environ.get("USERNAME")
            or ""
        )

        if self.environment == "windows":

            candidates = [
                Path("H:/"),
                Path("G:/"),
            ]

            expected_runtime = "windows"

        else:

            candidates = [
                Path("/mnt/g"),
                Path("/mnt/jarvis_runtime"),

                Path(f"/media/{username}/JARVIS_RUNTIME_L"),
                Path(f"/media/{username}/JARVIS_RUNTIME"),

                Path(f"/run/media/{username}/JARVIS_RUNTIME_L"),
                Path(f"/run/media/{username}/JARVIS_RUNTIME"),

                Path(f"/media/{username}/JARVIS_RUNTIME1"),
                Path(f"/run/media/{username}/JARVIS_RUNTIME1"),
            ]

            expected_runtime = "unix"

        for candidate in candidates:

            marker = candidate / ".jarvis_runtime"

            if not marker.exists():
                continue

            try:
                info = json.loads(marker.read_text())

                if info.get("runtime_type") == expected_runtime:
                    print(f"✓ Runtime discovered: {candidate}")
                    return candidate

            except Exception:
                continue

        return None
