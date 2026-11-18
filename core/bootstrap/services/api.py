from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


API_HOST = "127.0.0.1"
API_PORT = "8000"



def _bounty_api_environment():
    """Load Kali Bounty API credentials for the child process."""
    import stat

    env = os.environ.copy()

    credential_file = (
        Path.home()
        / ".config"
        / "jarvis"
        / "bounty-auth.env"
    )

    # Never load workstation-specific credentials on Ubuntu.
    from core.bootstrap.discovery.platform import detect_platform

    if detect_platform() != "kali":
        return env

    if not credential_file.is_file():
        raise RuntimeError(
            "Kali Bounty API credentials are missing"
        )

    mode = credential_file.stat().st_mode

    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise RuntimeError(
            "Bounty credential file permissions are unsafe"
        )

    allowed = {
        "JARVIS_BOUNTY_USER",
        "JARVIS_BOUNTY_PASSWORD",
    }

    values = {}

    for line in credential_file.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if not separator or key not in allowed:
            raise RuntimeError(
                "Invalid Bounty credential configuration"
            )

        if key in values:
            raise RuntimeError(
                "Duplicate Bounty credential setting"
            )

        values[key] = value

    if not values.get("JARVIS_BOUNTY_USER"):
        raise RuntimeError("Bounty username missing")

    if len(values.get("JARVIS_BOUNTY_PASSWORD", "")) < 32:
        raise RuntimeError("Bounty password is too short")

    env.update(values)
    return env


def launch_api(paths):
    print("Launching JARVIS API...")

    os.environ["PYTHONPATH"] = str(Path.cwd())

    print("=" * 60)
    print("Launcher sys.executable:", sys.executable)

    import uvicorn
    import openai

    print("Launcher uvicorn :", uvicorn.__file__)
    print("Launcher openai  :", openai.__file__)
    print("=" * 60)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "core.src.main:app",
            "--host",
            API_HOST,
            "--port",
            API_PORT,
        ],
        env=_bounty_api_environment(),
    )
