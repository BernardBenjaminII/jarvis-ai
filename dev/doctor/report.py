"""
JARVIS Doctor Report Renderer

Responsible only for presenting health check results.
"""

from .check import CheckResult
from collections import defaultdict 

class Report:
    def __init__(self):
        self.results: list[CheckResult] = []

    def add(self, result: CheckResult):
        self.results.append(result)

    def print(self):

        print()
        print("=" * 70)
        print("JARVIS DOCTOR")
        print("=" * 70)

        passed = 0
        failed = 0

        total_score = 0
        max_score = 0

        for result in self.results:
	    groups[result.category].append(result)
            symbol = "✓" if result.passed else "✗"

            print()
            print(f"{symbol} {result.name}")

            # Details
            for line in result.details:
                print(f"    {line}")

            # Warnings
            for line in result.warnings:
                print(f"    Warning: {line}")

            # Errors
            for line in result.errors:
                print(f"    Error: {line}")

            if result.passed:
                passed += 1
            else:
                failed += 1

            total_score += result.score
            max_score += result.max_score

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        print(f"Checks Passed : {passed}")
        print(f"Checks Failed : {failed}")

        if max_score:
            health = round((total_score / max_score) * 100)

            print(f"Overall Health: {health}%")

            if health >= 95:
                print("Status        : EXCELLENT")

            elif health >= 85:
                print("Status        : GOOD")

            elif health >= 70:
                print("Status        : FAIR")

            else:
                print("Status        : NEEDS ATTENTION")

        print("=" * 70)
