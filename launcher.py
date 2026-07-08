import os
import platform
import shutil
import subprocess
import sys
import time

from pathlib import Path

from core.bootstrap.services.api import launch_api
from core.bootstrap.discovery.paths import get_paths
from core.bootstrap.bootstrap_runner import BootstrapRunner
from core.bootstrap.discovery.platform import detect_platform
from core.src.cognition.model_registry import required_models
from core.src.cognition.capability_registry import detect_capabilities


# ============================================================
# CONFIGURATION
# ============================================================


API_HOST = "127.0.0.1"
API_PORT = "8000"


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
