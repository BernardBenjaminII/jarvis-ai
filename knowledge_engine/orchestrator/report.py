from __future__ import annotations

from datetime import datetime


class AssimilationReport:

    def __init__(self):
        self.started = datetime.utcnow()
        self.results = []

    def add(self, name: str, result: dict):
        self.results.append(
            {
                "stage": name,
                "result": result,
            }
        )

    def print(self):

        print()
        print("=" * 70)
        print("JARVIS ASSIMILATION REPORT")
        print("=" * 70)

        for item in self.results:

            print()

            print(item["stage"])

            for key, value in item["result"].items():
                print(f"   {key}: {value}")

        print()
