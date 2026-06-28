import os
import platform
import shutil
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from core.src.discovery.runtime_locator import RuntimeLocator

from core.src.cognition.model_registry import required_models
from core.src.cognition.capability_registry import detect_capabilities

def verify_capabilities():

    print("Checking capabilities...")

    capabilities = detect_capabilities()

    for capability, available in capabilities.items():

        status = "✓" if available else "✗"

        print(f"{status} {capability}")

    return capabilities

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_HOST = "http://127.0.0.1:11434"

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
# RUNTIME VERIFICATION
# ============================================================

def ensure_runtime(paths):
    print("Verifying runtime storage...")

    runtime = paths["runtime"]

    if not runtime.exists():
        print(f"Runtime path does not exist yet: {runtime}")
        print("Creating runtime directories...")

    directories = [
        paths["runtime"],
        paths["models"],
        paths["logs"],
        paths["vector_db"],
        paths["projects"],
        paths["venv"],
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    os.environ["OLLAMA_MODELS"] = str(paths["models"])

    print(f"Python  : {paths['python']}")
    print(f"Pip     : {paths['pip']}")
    print(f"Runtime : {paths['runtime']}")
    print(f"Models  : {paths['models']}")
    print(f"Venv    : {paths['venv']}")
    print("✓ Runtime storage available")

# ============================================================
# COMMAND CHECKS
# ============================================================

def ensure_command(command_name):
    if shutil.which(command_name) is None:
        print(f"✗ Required command not found in PATH: {command_name}")
        sys.exit(1)


# ============================================================
# OLLAMA
# ============================================================

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


# ============================================================
# MODEL VERIFICATION
# ============================================================
def ensure_models():
    print("Checking models...")

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
        )

    except subprocess.CalledProcessError:
        print("✗ Could not read Ollama model list")
        sys.exit(1)

    installed = result.stdout.lower()

    missing = []

    for model in required_models():

        if model.lower() in installed:
            print(f"✓ {model} available")
        else:
            print(f"✗ {model} missing")
            missing.append(model)

    if missing:

        print()
        print("Missing models:")

        for model in missing:
            print(f"  - {model}")

        print()
        print("Install missing models with:")

        for model in missing:
            print(f"  ollama pull {model}")

        sys.exit(1)

    print("✓ All required models available")



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
# ============================================================
# DEPENDENCIES
# ============================================================

def ensure_dependencies(paths):
    print("Checking Python dependencies...")

    requirements = Path("requirements.txt")

    if not requirements.exists():
        print("No requirements.txt found. Skipping dependency install.")
        return

    marker = Path(".venv") / ".deps_installed"

    if marker.exists():
        print("✓ Dependencies already installed")
        return

    print("Installing dependencies...")

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements),
        ],
        check=True,
    )

    marker.write_text("installed\n", encoding="utf-8")

    print("✓ Dependencies installed")


# ============================================================
# API
# ============================================================

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

    #
    # Runtime discovery
    #

    ensure_runtime(paths)

    #
    # Switch into the OS-specific runtime venv
    #

    ensure_venv(paths)

    #
    # Install/update dependencies if necessary
    #

    ensure_dependencies(paths)

    #
    # Third-party imports
    #

    global requests
    import requests

    #
    # Startup verification
    #

    ensure_ollama(paths)
    ensure_models()
    verify_capabilities()

    print("✓ Startup checks complete")

    #
    # Launch API
    #

    launch_api(paths)


if __name__ == "__main__":
    main()
