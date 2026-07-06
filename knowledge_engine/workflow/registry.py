from __future__ import annotations

from knowledge_engine.workflow.stage import WorkflowStage


class WorkflowRegistry:
    def __init__(self) -> None:
        self._stages: dict[str, WorkflowStage] = {}

    def register(self, stage: WorkflowStage) -> None:
        if stage.name in self._stages:
            raise ValueError(f"Workflow stage already registered: {stage.name}")
        self._stages[stage.name] = stage

    def all(self) -> list[WorkflowStage]:
        return list(self._stages.values())

    def resolve(self) -> list[WorkflowStage]:
        remaining = set(self._stages.keys())
        provided: set[str] = set()
        resolved: list[WorkflowStage] = []

        while remaining:
            runnable: list[WorkflowStage] = []

            for name in remaining:
                stage = self._stages[name]
                if stage.requires <= provided:
                    runnable.append(stage)

            if not runnable:
                blocked = {
                    name: sorted(self._stages[name].requires - provided)
                    for name in sorted(remaining)
                }
                raise RuntimeError(f"Unresolved workflow dependencies: {blocked}")

            runnable.sort(key=lambda stage: (stage.order, stage.name))

            for stage in runnable:
                resolved.append(stage)
                provided.update(stage.provides)
                remaining.remove(stage.name)

        return resolved
