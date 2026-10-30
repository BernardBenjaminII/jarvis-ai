#!/usr/bin/env python3
"""Resolve JARVIS Bluetooth adapters by their hardware MAC address."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/bluetooth/adapters.json"


def resolve(role):
    config = json.loads(CONFIG.read_text())
    target = config["controllers"][role]["address"].upper()

    result = subprocess.run(
        ["hciconfig", "-a"],
        capture_output=True,
        text=True,
        check=True,
    )

    current = None

    for line in result.stdout.splitlines():
        match = re.match(r"^(hci\d+):", line)

        if match:
            current = match.group(1)

        address_match = re.search(
            r"BD Address:\s*([0-9A-Fa-f:]{17})",
            line,
        )

        if address_match and current:
            if address_match.group(1).upper() == target:
                return current

    raise RuntimeError(
        f"DEDICATED_ADAPTER_UNAVAILABLE: {role} ({target})"
    )


if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "mobile_sensor"

    try:
        print(resolve(role))
    except (RuntimeError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
