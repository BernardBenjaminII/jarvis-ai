"""
runtime_context.py

Constructs the RuntimeContext object used throughout JARVIS.

This module is responsible for:
    - Discovering the runtime directory
    - Discovering the project directory
    - Gathering system information
    - Providing a single RuntimeContext object
"""

from pathlib import Path
import platform
import sys

from core.src.discovery.runtime_locator import RuntimeLocator
from core.src.runtime.runtime_models import (
    RuntimeContext,
    RuntimePaths,
    SystemInfo,
)


def get_runtime_context() -> RuntimeContext:
    """
    Build and return the current RuntimeContext.

    Returns:
        RuntimeContext
    """

    # ------------------------------------------------------
    # Determine environment
    # ------------------------------------------------------

    system = platform.system().lower()

    if system == "windows":
        environment = "windows"

    elif system == "darwin":
        environment = "macos"

    else:
        # Later we can distinguish ubuntu/kali/etc.
        environment = "ubuntu"

    # ------------------------------------------------------
    # Locate runtime
    # ------------------------------------------------------

    locator = RuntimeLocator(environment)
    runtime = locator.locate()

    if runtime is None:
        raise RuntimeError("Unable to locate JARVIS runtime.")

    # ------------------------------------------------------
    # Locate project
    # ------------------------------------------------------

    project = Path(__file__).resolve().parents[3]

    # ------------------------------------------------------
    # Build RuntimePaths
    # ------------------------------------------------------

    paths = RuntimePaths(
        runtime=runtime,
        project=project,
        knowledge=runtime / "knowledge",
        memory=runtime / "memory",
        models=runtime / "models",
        logs=runtime / "logs",
        venvs=runtime / "venvs",
        temp=runtime / "temp",
    )

    # ------------------------------------------------------
    # Build SystemInfo
    # ------------------------------------------------------

    system_info = SystemInfo(
        os_name=platform.system(),
        environment=environment,
        hostname=platform.node(),
        python=Path(sys.executable),
    )

    # ------------------------------------------------------
    # Return RuntimeContext
    # ------------------------------------------------------

    return RuntimeContext(
        paths=paths,
        system=system_info,
    )


# ------------------------------------------------------
# Singleton helper
# ------------------------------------------------------

_context: RuntimeContext | None = None


def context() -> RuntimeContext:
    """
    Return a cached RuntimeContext.

    Runtime discovery only occurs once.
    """

    global _context

    if _context is None:
        _context = get_runtime_context()

    return _context
