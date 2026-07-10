from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntegrityIssue:
    stage: str
    severity: str
    message: str
    file_path: str = ""
    record_id: str = ""
    preview: str = ""


@dataclass
class IntegrityReport:
    database_path: str
    documents_checked: int = 0
    chunks_checked: int = 0
    embeddings_checked: int = 0
    issues: list[IntegrityIssue] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[IntegrityIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    @property
    def warnings(self) -> list[IntegrityIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "warning"
        ]

    @property
    def passed(self) -> bool:
        return not self.errors
