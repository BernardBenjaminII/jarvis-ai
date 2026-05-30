import platform

def detect_os():
    system = platform.system().lower()

    if system == "windows":
        return "windows"

    elif system == "linux":
        try:
            with open("/etc/os-release") as f:
                data = f.read().lower()
                if "kali" in data:
                    return "kali"
                elif "ubuntu" in data:
                    return "ubuntu"
        except:
            pass
        return "linux"

    elif system == "darwin":
        return "macos"

    return "unknown"


CAPABILITY_PROFILES = {
    "windows": [
        "file_management",
        "office_automation",
        "email_handling",
        "basic_scripting"
    ],
    "ubuntu": [
        "development",
        "system_admin",
        "docker_control",
        "api_services"
    ],
    "kali": [
        "network_scanning",
        "packet_analysis",
        "offensive_security",
        "wireless_monitoring"
    ],
    "linux": [
        "general_linux_ops"
    ],
    "macos": [
        "development",
        "file_management"
    ],
    "unknown": []
}


MODES = {
    "windows": "assistant",
    "ubuntu": "engineer",
    "kali": "operator",
    "linux": "generic",
    "macos": "builder",
    "unknown": "neutral"
}


def get_environment():
    os_type = detect_os()
    capabilities = CAPABILITY_PROFILES.get(os_type, [])
    mode = MODES.get(os_type, "neutral")

    return {
        "os": os_type,
        "capabilities": capabilities,
        "mode": mode
    }
