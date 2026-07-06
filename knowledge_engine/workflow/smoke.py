from __future__ import annotations

from knowledge_engine.workflow.registry import WorkflowRegistry
from knowledge_engine.workflow.stage import WorkflowContext, WorkflowResult, WorkflowStage


class ReceivingSmokeStage(WorkflowStage):
    name = "receiving"
    order = 100
    provides = {"received"}

    def run(self, context: WorkflowContext) -> WorkflowResult:
        return WorkflowResult(
            name=self.name,
            metrics={"root": str(context.root), "accepted": 1},
        )


class DiscoverySmokeStage(WorkflowStage):
    name = "discovery"
    order = 200
    requires = {"received"}
    provides = {"discovered"}

    def run(self, context: WorkflowContext) -> WorkflowResult:
        return WorkflowResult(
            name=self.name,
            metrics={"files_seen": 1},
        )


class DoctorSmokeStage(WorkflowStage):
    name = "doctor"
    order = 900
    requires = {"discovered"}
    provides = {"doctor"}

    def run(self, context: WorkflowContext) -> WorkflowResult:
        return WorkflowResult(
            name=self.name,
            metrics={"health_score": 100},
        )


def build_smoke_registry() -> WorkflowRegistry:
    registry = WorkflowRegistry()
    registry.register(DoctorSmokeStage())
    registry.register(DiscoverySmokeStage())
    registry.register(ReceivingSmokeStage())
    return registry
