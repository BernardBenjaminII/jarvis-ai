from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


API_HOST = "127.0.0.1"
API_PORT = "8000"


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
        ]
    )
