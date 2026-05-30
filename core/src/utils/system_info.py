import platform
import psutil

def get_system_info():
    return {
        "os": platform.system(),
        "cpu": platform.processor(),
        "cores": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    }
