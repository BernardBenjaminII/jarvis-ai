from __future__ import annotations

import time

from knowledge_engine.director.report import AssimilationReport


class AssimilationDirector:

    def __init__(self, registry):

        self.registry = registry

    def run(self, context):

        report = AssimilationReport()

        for stage in self.registry.stages:

            print()

            print("=" * 70)

            print(stage.name)

            print("=" * 70)

            start = time.perf_counter()

            result = stage.run(context)

            result.elapsed = time.perf_counter() - start

            report.add(result)

            if not result.success:

                break

        return report
