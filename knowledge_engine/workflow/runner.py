from __future__ import annotations

import time

from knowledge_engine.workflow.registry import WorkflowRegistry
from knowledge_engine.workflow.stage import WorkflowContext, WorkflowResult


class WorkflowRunner:
    def __init__(self, registry: WorkflowRegistry) -> None:
        self.registry = registry

    def run(self, context: WorkflowContext) -> list[WorkflowResult]:
        results: list[WorkflowResult] = []

        for stage in self.registry.resolve():
            print()
            print("=" * 80)
            print(f"Workflow Stage: {stage.name}")
            print("=" * 80)

            start = time.perf_counter()

            try:
                result = stage.run(context)
                result.elapsed = time.perf_counter() - start
            except Exception as exc:
                result = WorkflowResult(
                    name=stage.name,
                    success=False,
                    errors=[str(exc)],
                    elapsed=time.perf_counter() - start,
                )

            results.append(result)

            context.metrics[stage.name] = {
                "success": result.success,
                "elapsed": result.elapsed,
                **result.metrics,
            }

            if not result.success:
                break

        return results
