from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssimilationReport:

    results: list = field(default_factory=list)

    def add(self, result):

        self.results.append(result)

    @property
    def successful(self):

        return all(r.success for r in self.results)

    def print(self):

        print()

        print("=" * 70)

        print("JARVIS ASSIMILATION REPORT")

        print("=" * 70)

        for result in self.results:

            print()

            print(result.name)

            print("-" * len(result.name))

            print(f"Success : {result.success}")

            print(f"Elapsed : {result.elapsed:.2f}s")

            for k, v in result.metrics.items():

                print(f"{k}: {v}")

            if result.warnings:

                print("Warnings:")

                for w in result.warnings:

                    print("  •", w)

            if result.errors:

                print("Errors:")

                for e in result.errors:

                    print("  •", e)
