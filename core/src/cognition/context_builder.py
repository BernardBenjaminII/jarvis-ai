from ..utils.environment import detect_environment
from ..utils.capabilities import detect_capabilities
from ..identity.loader import load_mode
from ..utils.network import is_online
from ..utils.system_info import get_system_info

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
