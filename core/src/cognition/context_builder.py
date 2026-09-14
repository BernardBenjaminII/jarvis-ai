"""Build live platform context without turning a machine role into a topic lock."""
from core.bootstrap.discovery.platform import detect_platform_details
from ..utils.capabilities import detect_capabilities
from ..identity.loader import load_mode
from ..utils.network import is_online
from ..utils.system_info import get_system_info
from .stance import resolve_stance


def build_context(stance=None, *, check_network=True):
    platform_info = detect_platform_details()
    environment = platform_info["environment"]
    selected = resolve_stance(environment, stance)
    # Existing custom profiles remain authoritative for automatic role/mission.
    # Generic Linux and unknown hosts need no new YAML to start conversation.
    profile_status = "loaded"
    try:
        mode = load_mode(environment)
    except FileNotFoundError:
        mode = {}
        profile_status = "missing; using built-in fallback"
    if not isinstance(mode, dict):
        raise ValueError(f"Invalid identity profile for {environment}: expected a mapping")
    mission = mode.get("mission", {})
    if not isinstance(mission, dict):
        raise ValueError(f"Invalid identity mission for {environment}: expected a mapping")
    manual = selected["source"] == "override"
    return {
        "environment": environment,
        "platform": platform_info,
        "stance": selected["name"],
        "stance_source": selected["source"],
        "profile_status": profile_status,
        "role": selected["role"] if manual else mode.get("role", selected["role"]),
        "mission": selected["mission"] if manual else mission.get("primary", selected["mission"]),
        "capabilities": detect_capabilities(),
        "capability_check": "executable presence on PATH only; not readiness or authorization",
        "system_info": get_system_info(),
        "online": is_online() if check_network else None,
    }
