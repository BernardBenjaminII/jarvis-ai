from __future__ import annotations

from knowledge_engine.orchestrator.report import AssimilationReport


class AssimilationPipeline:

    def __init__(self):
        self.stages = []

    def add_stage(self, stage):

        self.stages.append(stage)

    def run(self):

        report = AssimilationReport()

        for stage in self.stages:

            print()

            print("=" * 70)

            print(f"Running {stage.name}")

            print("=" * 70)

            result = stage.runner()

            report.add(stage.name, result)

        return report
