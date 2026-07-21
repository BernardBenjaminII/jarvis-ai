"""
GENESIS IV-R0-B COMPATIBILITY SHIM

The canonical implementation moved to:
    core.cognition.common.errors

This module preserves the established import path:
    core.cognition.errors
"""

from __future__ import annotations

from .common.errors import *  # noqa: F401,F403
from .common.errors import __all__ as __all__
