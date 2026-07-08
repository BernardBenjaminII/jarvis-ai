import os
import platform
import shutil
import subprocess
import sys
import time

from pathlib import Path

from core.src.discovery.runtime_locator import RuntimeLocator

from core.bootstrap.services.api import launch_api
from core.bootstrap.bootstrap_runner import BootstrapRunner

from core.src.cognition.model_registry import required_models
from core.src.cognition.capability_registry import detect_capabilities


# ============================================================
# CONFIGURATION
# ============================================================


API_HOST = "127.0.0.1"
API_PORT = "8000"

PLATFORM_INFO = {

    "windows": {
        "venv": "windows",
        "python": "Scripts/python.exe",
        "pip": "Scripts/pip.exe",
    },

    "ubuntu": {
        "venv": "ubuntu",
        "python": "bin/python",
        "pip": "bin/pip",
    },

    "kali": {
        "venv": "kali",
        "python": "bin/python",
        "pip": "bin/pip",
    },

    "macos": {
        "venv": "macos",
        "python": "bin/python",
        "pip": "bin/pip",
    },

    "linux": {
        "venv": "linux",
        "python": "bin/python",
        "pip": "bin/pip",
    },
}

# ============================================================
# PLATFORM DETECTION
# ============================================================

def detect_platform():
    system = platform.system()

    if system == "Windows":
        return "windows"

    if system == "Darwin":
        return "macos"

    if system == "Linux":
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                data = f.read().lower()

            if "kali" in data:
                return "kali"

            if "ubuntu" in data:
                return "ubuntu"

        except Exception:
            pass

        return "linux"

    return "unknown"


# ============================================================
# RUNTIME PATHS
# ============================================================

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

def get_paths(env):

    locator = RuntimeLocator(env)
    runtime = locator.locate()

    if runtime is None:
        raise RuntimeError("No compatible JARVIS runtime found.")

    if env not in PLATFORM_INFO:
        raise RuntimeError(f"Unsupported platform: {env}")

    info = PLATFORM_INFO[env]

    venv = runtime / "venvs" / info["venv"]

    return {
        "runtime": runtime,
        "venv": venv,
        "python": venv / info["python"],
        "pip": venv / info["pip"],

        "models": runtime / "ollama" / "models",
        "logs": runtime / "logs",
        "vector_db": runtime / "vector_db",
        "projects": runtime / "projects",
    }


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 50)
    print("JARVIS INITIALIZATION")
    print("=" * 50)

    env = detect_platform()
    paths = get_paths(env)

    print(f"Environment: {env}")


    BootstrapRunner(env, paths).run()

    #
    # Launch API
    #

    launch_api(paths)


if __name__ == "__main__":
    main()
