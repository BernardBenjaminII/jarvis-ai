# core/src/tools/macos_tools.py
from core.src.services.macos.system import (
    macos_system_profile,
    macos_battery_status,
    macos_wifi_status,
    macos_open_app,
    macos_say,
    macos_open_path,
)


def run_macos_tool(command: str, argument: str = "") -> str:
    command = command.lower().strip()

    if command == "system_profile":
        return macos_system_profile()

    if command == "battery":
        return macos_battery_status()

    if command == "wifi":
        return macos_wifi_status()

    if command == "open_app":
        return macos_open_app(argument)

    if command == "say":
        return macos_say(argument)

    if command == "open_path":
        return macos_open_path(argument)

    return f"Unknown macOS tool: {command}"
