"""
JARVIS Doctor Report Renderer

Responsible only for presenting health check results.
"""

from collections import defaultdict

from .check import CheckResult


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

        # ----------------------------------------------------------
        # Group results by category
        # ----------------------------------------------------------

        groups = defaultdict(list)

        for result in self.results:
            groups[result.category].append(result)

        # ----------------------------------------------------------
        # Print categories
        # ----------------------------------------------------------

        for category in sorted(groups):

            print()
            print(category)
            print("-" * len(category))

            for result in groups[category]:

                symbol = "✓" if result.passed else "✗"

                print()
                print(f"{symbol} {result.name}")

                if result.details:
                    print("    Details:")
                    for line in result.details:
                        print(f"        • {line}")

                if result.warnings:
                    print("    Warnings:")
                    for line in result.warnings:
                        print(f"        • {line}")

                if result.errors:
                    print("    Errors:")
                    for line in result.errors:
                        print(f"        • {line}")

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
                status = "EXCELLENT"
            elif health >= 85:
                status = "GOOD"
            elif health >= 70:
                status = "FAIR"
            else:
                status = "NEEDS ATTENTION"

            print(f"Status        : {status}")

        print("=" * 70)
