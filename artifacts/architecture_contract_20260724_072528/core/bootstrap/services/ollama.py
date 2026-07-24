from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import time

import requests

OLLAMA_HOST = "http://127.0.0.1:11434"

# ============================================================
# OLLAMA
# ============================================================

def ensure_command(command_name):
    if shutil.which(command_name) is None:
        print(f"✗ Required command not found in PATH: {command_name}")
        sys.exit(1)


def ollama_running():
    try:
        response = requests.get(
            f"{OLLAMA_HOST}/api/tags",
            timeout=2,
        )
        return response.status_code == 200

    except Exception:
        return False


def ensure_ollama(paths):
    print("Checking Ollama...")

    ensure_command("ollama")

    if ollama_running():
        print("✓ Ollama already running")
        return

    print("Starting Ollama...")

    log_file = paths["logs"] / "ollama.log"

    try:
        if platform.system() == "Windows":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=open(log_file, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=open(log_file, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
            )

    except Exception as exc:
        print(f"✗ Failed to start Ollama: {exc}")
        sys.exit(1)

    time.sleep(5)

    if not ollama_running():
        print("✗ Ollama failed to start")
        print(f"Check log: {log_file}")
        sys.exit(1)

    print("✓ Ollama online")


