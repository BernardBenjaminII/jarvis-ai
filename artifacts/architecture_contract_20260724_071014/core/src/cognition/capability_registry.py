import shutil


CAPABILITIES = {
    "ollama": "ollama",
    "git": "git",
    "python": "python",
    "nmap": "nmap",
    "subfinder": "subfinder",
    "amass": "amass",
    "httpx": "httpx",
    "nuclei": "nuclei",
}


def detect_capabilities():

    available = {}

    for capability, command in CAPABILITIES.items():

        available[capability] = (
            shutil.which(command) is not None
        )

    return available