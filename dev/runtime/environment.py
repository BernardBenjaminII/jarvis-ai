from __future__ import annotations

import platform
import sys
from pathlib import Path


def python_executable() -> Path:
    return Path(sys.executable).resolve()


def python_version() -> str:
    return platform.python_version()


def runtime_platform() -> str:
    return platform.platform()
