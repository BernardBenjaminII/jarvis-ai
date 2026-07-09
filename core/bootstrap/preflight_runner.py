from __future__ import annotations

from .preflight.python_check import PythonCheck
from .preflight.runtime_check import RuntimeMountCheck


class BootstrapRunner:

    def __init__(self):

        self.checks = [

            PythonCheck(),

            RuntimeMountCheck(),

        ]

    def run(self):

        failures = []

        print()
        print("=" * 70)
        print("JARVIS PRE-FLIGHT")
        print("=" * 70)

        for check in self.checks:

            result = check.run()

            state = "PASS" if result.passed else "FAIL"

            print(
                f"{state:5} "
                f"{result.stage:12}"
                f"{result.name:25}"
                f"{result.duration_ms:7.1f} ms   "
                f"{result.message}"
            )

            if not result.passed and result.fatal:

                failures.append(result)

        print("-" * 70)

        if failures:

            print(f"{len(failures)} fatal check(s) failed.")

            return False

        print("Preflight successful.")

        return True
