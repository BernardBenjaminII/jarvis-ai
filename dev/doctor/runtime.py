from pathlib import Path

from .check import HealthCheck
from .check import CheckResult


class RuntimeCheck(HealthCheck):

    name = "Runtime"

    def run(self):

        runtime = Path("/media/abdullah/JARVIS_RUNTIME_L")

        if runtime.exists():

            return CheckResult(
                name=self.name,
                passed=True,
                score=100,
                details=[
                    str(runtime),
                ],
            )

        return CheckResult(
            name=self.name,
            passed=False,
            score=0,
            errors=[
                "Runtime directory not found",
            ],
        )
