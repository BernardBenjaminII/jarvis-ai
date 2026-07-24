# core/src/services/macos/system.py

import platform
import subprocess
from pathlib import Path


def is_macos() -> bool:
    return platform.system().lower() == "darwin"


def run_cmd(cmd: list[str], input_text: str | None = None) -> str:
    if not is_macos():
        return "This function only works on macOS."

    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        output = (result.stdout or "").strip()

        if not output:
            output = (result.stderr or "").strip()

        return output

    except Exception as e:
        return f"Command failed: {e}"


# ------------------------------------------------------------------
# SYSTEM
# ------------------------------------------------------------------

def macos_system_profile() -> str:
    return run_cmd(["system_profiler", "SPHardwareDataType"])


def macos_system_status() -> str:

    battery = macos_battery_status()

    cpu = run_cmd([
        "sysctl",
        "-n",
        "machdep.cpu.brand_string"
    ])

    ram_bytes = run_cmd([
        "sysctl",
        "-n",
        "hw.memsize"
    ])

    uptime = run_cmd([
        "uptime"
    ])

    try:
        ram_gb = round(int(ram_bytes) / (1024 ** 3), 1)
        ram = f"{ram_gb} GB"
    except Exception:
        ram = ram_bytes

    return f"""
JARVIS macOS Status
===================

CPU:
{cpu}

RAM:
{ram}

Battery:
{battery}

Uptime:
{uptime}
""".strip()


# ------------------------------------------------------------------
# BATTERY
# ------------------------------------------------------------------

def macos_battery_status() -> str:
    return run_cmd(["pmset", "-g", "batt"])


# ------------------------------------------------------------------
# WIFI
# ------------------------------------------------------------------

def macos_wifi_status() -> str:

    # Try wdutil first
    output = run_cmd(["wdutil", "info"])

    if (
        output
        and "usage:" not in output.lower()
        and "permission denied" not in output.lower()
    ):
        return output

    # Fallback
    return macos_wifi_summary()


def macos_wifi_summary() -> str:

    network = run_cmd([
        "networksetup",
        "-getairportnetwork",
        "en0"
    ])

    ip = run_cmd([
        "ipconfig",
        "getifaddr",
        "en0"
    ])

    return f"""
WiFi Status
-----------
{network}

IP Address:
{ip}
""".strip()


# ------------------------------------------------------------------
# APPS
# ------------------------------------------------------------------

def macos_open_app(app_name: str) -> str:
    return run_cmd(["open", "-a", app_name])


def macos_open_path(path: str) -> str:

    expanded = str(
        Path(path).expanduser()
    )

    return run_cmd([
        "open",
        expanded
    ])


# ------------------------------------------------------------------
# VOICE
# ------------------------------------------------------------------

def macos_say(text: str) -> str:
    return run_cmd(["say", text])


def macos_say_voice(
    text: str,
    voice: str = "Daniel"
) -> str:

    return run_cmd([
        "say",
        "-v",
        voice,
        text
    ])


# ------------------------------------------------------------------
# CLIPBOARD
# ------------------------------------------------------------------

def macos_clipboard_read() -> str:
    return run_cmd(["pbpaste"])


def macos_clipboard_write(text: str) -> str:

    try:
        subprocess.run(
            ["pbcopy"],
            input=text,
            text=True,
            check=True
        )

        return "Copied to clipboard."

    except Exception as e:
        return f"Clipboard write failed: {e}"


# ------------------------------------------------------------------
# NOTIFICATIONS
# ------------------------------------------------------------------

def macos_notify(
    title: str,
    message: str
) -> str:

    script = (
        f'display notification "{message}" '
        f'with title "{title}"'
    )

    return run_cmd([
        "osascript",
        "-e",
        script
    ])


# ------------------------------------------------------------------
# SCREENSHOTS
# ------------------------------------------------------------------

def macos_screenshot(
    path: str = "~/Desktop/jarvis_capture.png"
) -> str:

    expanded = str(
        Path(path).expanduser()
    )

    run_cmd([
        "screencapture",
        expanded
    ])

    return expanded


# ------------------------------------------------------------------
# FINDER / SPOTLIGHT
# ------------------------------------------------------------------

def macos_find(query: str) -> str:
    return run_cmd([
        "mdfind",
        query
    ])
