"""
GENESIS IV-R0-B COMPATIBILITY SHIM

The canonical implementation moved to:
    core.cognition.common.normalization

This module preserves the established import path:
    core.cognition.normalization
"""

from __future__ import annotations

from .common.normalization import *  # noqa: F401,F403
from .common.normalization import __all__ as __all__
