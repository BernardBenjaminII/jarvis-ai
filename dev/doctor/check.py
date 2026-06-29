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

    # Required fields
    name: str
    passed: bool

    # Metadata
    category: str = "General"
    description: str = ""

    # Health score
    score: int = 0
    max_score: int = 100

    # Informational output
    details: list[str] = field(default_factory=list)

    # Non-fatal issues
    warnings: list[str] = field(default_factory=list)

    # Fatal issues
    errors: list[str] = field(default_factory=list)

    # Help for the user
    fix_hint: str = ""
    documentation: str = ""


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

    def __init__(self):
        self._result = CheckResult(
            name=self.name,
            passed=True,
            category=self.category,
            description=self.description,
            fix_hint=self.fix_hint,
            documentation=self.documentation,
        )

    def detail(self, text: str):
        self._result.details.append(text)

    def warn(self, text: str):
        self._result.warnings.append(text)

    def fail(self, text: str):
        self._result.passed = False
        self._result.errors.append(text)

    def score(self, value: int, maximum: int = 100):
        self._result.score = value
        self._result.max_score = maximum

    def result(self):
        return self._result

    @abstractmethod
    def run(self):
        ...
