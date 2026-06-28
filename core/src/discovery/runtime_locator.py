"""
runtime_locator.py

Responsible for discovering the JARVIS runtime directory.

This class searches a list of known locations for a valid
JARVIS runtime by looking for a .jarvis_runtime marker file.
"""

from pathlib import Path
import json
import os


class RuntimeLocator:
    """Locate the JARVIS runtime directory."""

    def __init__(self, environment: str):
        self.environment = environment

    def locate(self) -> Path | None:
        """
        Locate the correct runtime directory.

        Returns:
            Path: Runtime directory if found.
            None: If no valid runtime is discovered.
        """

        # Environment override always wins
        env_override = os.environ.get("JARVIS_RUNTIME")
        if env_override:
            runtime = Path(env_override)

            if runtime.exists():
                print(f"✓ Runtime override: {runtime}")
                return runtime

        username = (
            os.environ.get("USER")
            or os.environ.get("USERNAME")
            or ""
        )

        # ------------------------------------------------------
        # Candidate locations
        # ------------------------------------------------------

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

                # Fallback names
                Path(f"/media/{username}/JARVIS_RUNTIME1"),
                Path(f"/run/media/{username}/JARVIS_RUNTIME1"),
            ]

            expected_runtime = "unix"

        # ------------------------------------------------------
        # Search each candidate
        # ------------------------------------------------------

        for candidate in candidates:

            marker = candidate / ".jarvis_runtime"

            if not marker.exists():
                continue

            try:

                info = json.loads(marker.read_text())

                if info.get("runtime_type") == expected_runtime:

                    print(f"✓ Runtime discovered: {candidate}")

                    return candidate

            except Exception as exc:
                print(f"Warning: Failed reading {marker}: {exc}")

        # Nothing found
        return None
