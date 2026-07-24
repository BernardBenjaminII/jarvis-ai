"""
Canonical JARVIS verification framework.

The framework executes existing phase verification scripts through one
registry and produces consistent console and JSON reports.
"""

from dev.verification.models import (
    SuiteDefinition,
    SuiteResult,
    VerificationReport,
)
from dev.verification.registry import (
    VERIFICATION_SUITES,
)

__all__ = [
    "SuiteDefinition",
    "SuiteResult",
    "VerificationReport",
    "VERIFICATION_SUITES",
]
