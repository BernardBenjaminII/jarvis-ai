import os
import platform

# --------------------------------
# Shared JARVIS Home
# --------------------------------

if platform.system().lower() == "windows":
    BASE = r"E:\JARVIS_HOME"

elif platform.system().lower() == "linux":
    BASE = "/mnt/shared200/JARVIS_HOME"

elif platform.system().lower() == "darwin":
    BASE = os.path.expanduser("~/JARVIS_HOME")

else:
    BASE = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

# --------------------------------
# Runtime Paths
# --------------------------------

PATHS = {
    "models": os.path.join(BASE, "models"),
    "memory": os.path.join(BASE, "memory"),
    "identity": os.path.join(BASE, "identity"),
    "logs": os.path.join(BASE, "logs"),
    "knowledge": os.path.join(BASE, "knowledge"),
    "agents": os.path.join(BASE, "agents"),
    "vector_db": os.path.join(BASE, "vector_db"),
}