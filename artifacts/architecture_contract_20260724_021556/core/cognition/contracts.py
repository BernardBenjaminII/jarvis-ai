"""
GENESIS IV-R0-B COMPATIBILITY SHIM

The canonical implementation moved to:
    core.cognition.common.contracts

This module preserves the established import path:
    core.cognition.contracts
"""

from __future__ import annotations

from .common.contracts import *  # noqa: F401,F403
from .common.contracts import __all__ as __all__
