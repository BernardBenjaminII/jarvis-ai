import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PATHS = {
    "models": os.path.join(BASE, "models"),
    "memory": os.path.join(BASE, "memory"),
    "identity": os.path.join(BASE, "identity"),
    "logs": os.path.join(BASE, "logs"),
}
