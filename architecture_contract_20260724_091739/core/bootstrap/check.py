from __future__ import annotations

import time
from abc import ABC, abstractmethod

from .models import CheckResult


class BootstrapCheck(ABC):

    stage = "unknown"
    name = "unnamed"
    fatal = True

    def run(self) -> CheckResult:

        start = time.perf_counter()

        try:
            passed, message = self.execute()

        except Exception as exc:

            passed = False
            message = str(exc)

        elapsed = (time.perf_counter() - start) * 1000

        return CheckResult(
            stage=self.stage,
            name=self.name,
            passed=passed,
            message=message,
            fatal=self.fatal,
            duration_ms=elapsed,
        )

    @abstractmethod
    def execute(self) -> tuple[bool, str]:
        ...
