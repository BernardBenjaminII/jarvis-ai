import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from core.src.cognition.model_registry import required_models
from core.src.cognition.capability_registry import detect_capabilities

try:
    import requests
except ImportError:
    print("ERROR: requests is not installed.")
    print("Run: pip install requests")
    sys.exit(1)


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

def get_runtime_root(env):
    env_override = os.environ.get("JARVIS_RUNTIME")

    if env_override:
        return Path(env_override)

    if env == "windows":
        return Path("H:/JARVIS_HOME")

    if env == "macos":
        return Path("/Volumes/JARVISDATA")

    return Path("/mnt/g")


def get_paths(env):
    runtime = get_runtime_root(env)

    return {
        "runtime": runtime,
        "models": runtime / "ollama" / "models",
        "logs": runtime / "logs",
        "vector_db": runtime / "vector_db",
        "venvs": runtime / "venvs",
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

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    os.environ["OLLAMA_MODELS"] = str(paths["models"])

    print(f"Runtime: {paths['runtime']}")
    print(f"Models : {paths['models']}")
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

def ensure_venv():
    print("Checking virtual environment...")

    if sys.prefix == sys.base_prefix:
        print()
        print("WARNING: Not running inside a virtual environment")
        print("Activate with:")
        print("  .\\.venv\\Scripts\\Activate.ps1")
        print()
    else:
        print("✓ Virtual environment active")


# ============================================================
# DEPENDENCIES
# ============================================================

def ensure_dependencies():
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

def launch_api():
    print("Launching JARVIS API...")

    os.environ["PYTHONPATH"] = str(Path.cwd())

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
            "--reload",
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

    ensure_runtime(paths)
    ensure_ollama(paths)
    ensure_models()
    verify_capabilities()
    ensure_venv()
    ensure_dependencies()

    print("✓ Startup checks complete")

    launch_api()


if __name__ == "__main__":
    main()
