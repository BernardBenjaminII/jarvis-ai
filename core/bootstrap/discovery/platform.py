"""Canonical, read-only host detection shared by startup and conversation."""
from __future__ import annotations

from pathlib import Path
import platform


def _release_fields(path="/etc/os-release"):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}
    fields = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in {"ID", "ID_LIKE", "VERSION_ID", "DISTRIB_ID"}:
            fields[key.strip()] = value.strip().strip('"').strip("'").lower()
    return fields


def detect_platform_details() -> dict:
    system = platform.system().lower()
    release = platform.release()
    fields = _release_fields() if system == "linux" else {}
    distro = fields.get("ID", "")
    if system == "linux" and not distro:
        distro = _release_fields("/etc/lsb-release").get("DISTRIB_ID", "")
    # Family hints are descriptive; Mint/Debian must not become Ubuntu/Kali.
    environment = {"windows": "windows", "darwin": "macos"}.get(system, "unknown")
    if system == "linux":
        environment = distro if distro in {"kali", "ubuntu"} else "linux"
    return {
        "environment": environment,
        "os": system or "unknown",
        "distribution": distro or None,
        "distribution_family": fields.get("ID_LIKE", "").split(),
        "version": fields.get("VERSION_ID") or None,
        "architecture": platform.machine(),
        "kernel": release,
        "wsl": system == "linux" and "microsoft" in release.lower(),
    }


def detect_platform() -> str:
    return detect_platform_details()["environment"]
