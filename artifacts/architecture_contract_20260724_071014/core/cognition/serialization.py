"""
GENESIS IV-R0-B COMPATIBILITY SHIM

The canonical implementation moved to:
    core.cognition.common.serialization

This module preserves the established import path:
    core.cognition.serialization
"""

from __future__ import annotations

from .common.serialization import *  # noqa: F401,F403
from .common.serialization import __all__ as __all__
