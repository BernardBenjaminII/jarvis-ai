import platform

from .check import HealthCheck
from .check import CheckResult


class EnvironmentCheck(HealthCheck):

    name = "Environment"

    def run(self):

        return CheckResult(
            name=self.name,
            passed=True,
            score=100,
            details=[
                platform.platform(),
            ],
        )
