from __future__ import annotations

from knowledge_engine.workflow.stage import WorkflowResult


def print_workflow_report(results: list[WorkflowResult]) -> None:
    print()
    print("=" * 80)
    print("JARVIS WORKFLOW REPORT")
    print("=" * 80)

    for result in results:
        print()
        print(result.name)
        print("-" * len(result.name))
        print(f"Success : {result.success}")
        print(f"Elapsed : {result.elapsed:.2f}s")

        for key, value in result.metrics.items():
            print(f"{key}: {value}")

        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
