from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkflowStageReport:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class WorkflowReport:
    name: str
    stages: list[WorkflowStageReport] = field(default_factory=list)

    def add(self, stage: WorkflowStageReport) -> None:
        self.stages.append(stage)

    @property
    def passed(self) -> bool:
        return all(stage.passed for stage in self.stages)

    def print(self) -> None:
        print()
        print("=" * 70)
        print(self.name)
        print("=" * 70)

        for stage in self.stages:
            symbol = "✓" if stage.passed else "✗"
            print()
            print(f"{symbol} {stage.name}")

            for detail in stage.details:
                print(f"    • {detail}")

            for error in stage.errors:
                print(f"    ERROR: {error}")

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Stages Passed: {sum(1 for s in self.stages if s.passed)}")
        print(f"Stages Failed: {sum(1 for s in self.stages if not s.passed)}")
        print(f"Overall      : {'PASS' if self.passed else 'FAIL'}")
        print("=" * 70)
