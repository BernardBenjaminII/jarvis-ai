from __future__ import annotations

from knowledge_engine.doctor.checks import run_checks

from knowledge_engine.director.stage import (
    AssimilationStage,
    StageResult,
)


class DoctorStage(AssimilationStage):

    name = "Knowledge Doctor"

    order = 1000

    def run(self, context):

        report = run_checks(context.database)

        return StageResult(

            name=self.name,

            success=True,

            metrics=report,
        )
