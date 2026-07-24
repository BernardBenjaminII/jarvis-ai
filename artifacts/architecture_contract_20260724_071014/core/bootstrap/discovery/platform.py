from __future__ import annotations

import platform


def detect_platform() -> str:
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
