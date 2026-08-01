"""
Compatibility bridge for Genesis VII-A0 Pack 2.

Application bootstrap code should import `router` from this module. The actual
implementation remains isolated in the Executive Operations Center package.
"""

from core.executive.operations_center.api import (
    EXECUTIVE_API_PREFIX,
    EXECUTIVE_API_TAG,
    router,
    runtime,
)

__all__ = [
    "EXECUTIVE_API_PREFIX",
    "EXECUTIVE_API_TAG",
    "router",
    "runtime",
]
