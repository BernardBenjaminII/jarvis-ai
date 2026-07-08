from __future__ import annotations

from core.bootstrap.discovery.locator import RuntimeLocator


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
