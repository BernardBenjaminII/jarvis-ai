import json
import os
import platform
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def detect_platform():

    system = platform.system()

    if system == "Windows":
        return "windows"

    if system == "Darwin":
        return "macos"

    with open("/etc/os-release") as f:
        data = f.read().lower()

    if "kali" in data:
        return "kali"

    return "ubuntu"


def load_platform_config():

    platform_name = detect_platform()

    config_file = CONFIG_DIR / f"{platform_name}.json"

    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)

    username = os.getenv("USER") or os.getenv("USERNAME")

    def expand(value):
        return value.replace("%USER%", username)

    if "runtime_candidates" in config:

        for path in config["runtime_candidates"]:

            path = expand(path)

            if Path(path).exists():

                config["runtime"] = path
                break

    if "project_candidates" in config:

        for path in config["project_candidates"]:

            path = expand(path)

            if Path(path).exists():

                config["project"] = path
                break

    return config
