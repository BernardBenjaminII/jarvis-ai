import importlib

from .check import HealthCheck
from .check import CheckResult


MODULES = [
    "fastapi",
    "uvicorn",
    "requests",
    "openai",
    "psutil",
]


class ImportCheck(HealthCheck):

    name = "Python Dependencies"

    def run(self):

        missing = []

        for module in MODULES:

            try:
                importlib.import_module(module)
            except Exception:
                missing.append(module)

        if missing:

            return CheckResult(
                name=self.name,
                passed=False,
                score=0,
                errors=missing,
            )

        return CheckResult(
            name=self.name,
            passed=True,
            score=100,
        )
