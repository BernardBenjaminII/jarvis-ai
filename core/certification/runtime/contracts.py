from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class CertificationRuntimeError(RuntimeError):
    """Base error for the certification runtime."""


class RepositoryNotFoundError(CertificationRuntimeError):
    """Raised when the canonical JARVIS repository cannot be found."""


@dataclass(frozen=True, slots=True)
class BootstrapCheck:
    code: str
    label: str
    status: str
    detail: str
    actual: Any = None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BootstrapReport:
    repository_root: str
    python_executable: str
    python_version: str
    initial_cwd: str
    effective_cwd: str
    virtual_environment: str | None
    runtime_root: str | None
    knowledge_root: str | None
    catalog_database: str | None
    checks: tuple[BootstrapCheck, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        return "EXCELLENT" if all(item.passed for item in self.checks) else "FAILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "repository_root": self.repository_root,
            "python_executable": self.python_executable,
            "python_version": self.python_version,
            "initial_cwd": self.initial_cwd,
            "effective_cwd": self.effective_cwd,
            "virtual_environment": self.virtual_environment,
            "runtime_root": self.runtime_root,
            "knowledge_root": self.knowledge_root,
            "catalog_database": self.catalog_database,
            "checks": [item.to_dict() for item in self.checks],
        }
