# core/src/utils/capabilities.py

import shutil


TOOLS = [
    "nmap",
    "subfinder",
    "amass",
    "httpx",
    "katana",
    "nuclei",
    "docker",
    "ollama",
]


def detect_capabilities():

    detected = {}

    for tool in TOOLS:
        detected[tool] = shutil.which(tool) is not None

    return detected
