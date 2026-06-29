"""
JARVIS Doctor Framework

Defines the base classes used by all health checks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    """
    Result returned by every HealthCheck.
    """

    # Human-readable name of the check
    name: str

    # Overall pass/fail
    passed: bool

    # Health score
    score: int = 0
    max_score: int = 100

    # Informational output
    details: list[str] = field(default_factory=list)

    # Non-fatal issues
    warnings: list[str] = field(default_factory=list)

    # Fatal issues
    errors: list[str] = field(default_factory=list)


class HealthCheck(ABC):
    """
    Base class for every JARVIS Doctor health check.
    """

    name = "Unnamed Check"

    description = ""

    category = "General"

    order = 100

    critical = False

    fix_hint = ""

    documentation = ""

    @abstractmethod
    def run(self) -> CheckResult:
        """
        Execute the health check and return a CheckResult.
        """
        raise NotImplementedError
