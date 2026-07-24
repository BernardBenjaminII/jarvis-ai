# core/src/utils/environment.py

import os
import platform


def detect_environment():

    system = platform.system().lower()

    # -----------------------------
    # Linux
    # -----------------------------
    if system == "linux":

        # Primary detection
        if os.path.exists("/etc/os-release"):

            with open("/etc/os-release", "r") as f:
                data = f.read().lower()

                if "kali" in data:
                    return "kali"

                if "ubuntu" in data:
                    return "ubuntu"

        # Secondary fallback
        if os.path.exists("/etc/lsb-release"):

            with open("/etc/lsb-release", "r") as f:
                data = f.read().lower()

                if "ubuntu" in data:
                    return "ubuntu"

        return "linux"

    # -----------------------------
    # Windows
    # -----------------------------
    elif system == "windows":
        return "windows"

    # -----------------------------
    # Apple
    # -----------------------------
    elif system == "darwin":
        return "macos"

    # -----------------------------
    # Unknown
    # -----------------------------
    return "unknown"
