"""
Immutable data models used by the JARVIS verification framework.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


SuiteStatus = Literal[
    "passed",
    "failed",
    "skipped",
    "missing",
]


@dataclass(frozen=True)
class SuiteDefinition:
    """One registered verification suite."""

    suite_id: str
    name: str
    script_path: str
    required: bool = True
    category: str = "core"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.suite_id.strip():
            raise ValueError("suite_id must not be empty")

        if not self.name.strip():
            raise ValueError("name must not be empty")

        if not self.script_path.strip():
            raise ValueError("script_path must not be empty")

        if not self.category.strip():
            raise ValueError("category must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SuiteResult:
    """Result of executing one registered verification suite."""

    suite_id: str
    name: str
    script_path: str
    required: bool
    category: str
    status: SuiteStatus
    return_code: int | None
    elapsed_seconds: float
    stdout: str
    stderr: str
    failure_reason: str | None = None

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    @property
    def blocks_success(self) -> bool:
        if not self.required:
            return False

        return self.status in {
            "failed",
            "missing",
        }

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        data["blocks_success"] = self.blocks_success
        return data


@dataclass(frozen=True)
class VerificationReport:
    """Complete master-verification result."""

    framework_version: str
    started_at: str
    completed_at: str
    elapsed_seconds: float
    repository_root: str
    git_commit: str | None
    git_branch: str | None
    git_dirty: bool | None
    selected_suite_ids: tuple[str, ...]
    results: tuple[SuiteResult, ...]

    @property
    def suites_executed(self) -> int:
        return sum(
            result.status
            not in {
                "skipped",
                "missing",
            }
            for result in self.results
        )

    @property
    def suites_passed(self) -> int:
        return sum(
            result.status == "passed"
            for result in self.results
        )

    @property
    def suites_failed(self) -> int:
        return sum(
            result.blocks_success
            for result in self.results
        )

    @property
    def suites_skipped(self) -> int:
        return sum(
            result.status == "skipped"
            for result in self.results
        )

    @property
    def suites_missing(self) -> int:
        return sum(
            result.status == "missing"
            for result in self.results
        )

    @property
    def passed(self) -> bool:
        return self.suites_failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_version": self.framework_version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "elapsed_seconds": self.elapsed_seconds,
            "repository_root": self.repository_root,
            "git": {
                "commit": self.git_commit,
                "branch": self.git_branch,
                "dirty": self.git_dirty,
            },
            "selected_suite_ids": list(
                self.selected_suite_ids
            ),
            "summary": {
                "suites_executed": self.suites_executed,
                "suites_passed": self.suites_passed,
                "suites_failed": self.suites_failed,
                "suites_skipped": self.suites_skipped,
                "suites_missing": self.suites_missing,
                "passed": self.passed,
            },
            "results": [
                result.to_dict()
                for result in self.results
            ],
        }
