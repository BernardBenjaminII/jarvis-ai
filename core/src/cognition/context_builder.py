from src.utils.environment import detect_environment
from src.utils.capabilities import detect_capabilities
from src.identity.loader import load_mode
from src.utils.network import is_online
from src.utils.system_info import get_system_info


def build_context():

    environment = detect_environment()

    mode = load_mode(environment)

    capabilities = detect_capabilities()

    system_info = get_system_info()

    online = is_online()

    context = {
        "environment": environment,
        "role": mode["role"],
        "mission": mode["mission"]["primary"],
        "capabilities": capabilities,
        "system_info": system_info,
        "online": online,
    }

    return context
