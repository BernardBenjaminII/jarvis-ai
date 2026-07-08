from __future__ import annotations

from .context import KnowledgeContext
from .report import WorkflowReport, WorkflowStageReport
from .stage import WorkflowStage


class WorkflowRunner:
    def __init__(self, name: str, stages: list[WorkflowStage]):
        self.name = name
        self.stages = stages

    def run(self, context: KnowledgeContext) -> tuple[KnowledgeContext, WorkflowReport]:
        report = WorkflowReport(self.name)

        for stage in self.stages:
            before_errors = len(context.errors)

            try:
                context = stage.run(context)
            except Exception as exc:
                context.fail(f"{stage.name}: {exc}")

            new_errors = context.errors[before_errors:]
            passed = not new_errors

            report.add(
                WorkflowStageReport(
                    name=stage.name,
                    passed=passed,
                    details=[f"context.ok={context.ok}"],
                    errors=new_errors,
                )
            )

            if not passed:
                break

        return context, report
