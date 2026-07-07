from pathlib import Path
import os
import subprocess
import sys

# ============================================================
# VIRTUAL ENVIRONMENT
# ============================================================

def ensure_venv(paths):
    print("Checking runtime virtual environment...")

    python = paths["python"]

    #
    # Create the venv if it doesn't exist
    #

    if not python.exists():

        print("Creating runtime virtual environment...")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "venv",
                str(paths["venv"]),
            ],
            check=True,
        )

    #
    # Are we already running from this venv?
    #
    current = Path(sys.executable)
    target = python

    print("Current:", current)
    print("Target :", target)

    if current != target:
        print("Switching to runtime Python...")
        os.execv(str(target), [str(target)] + sys.argv)

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


