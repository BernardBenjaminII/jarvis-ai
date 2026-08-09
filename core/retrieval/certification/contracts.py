from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CertificationCheck:
    code: str
    label: str
    status: str
    detail: str
    expected: Any = None
    actual: Any = None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EndToEndCertificationReport:
    schema_version: str
    generated_at: str
    repository_root: str
    catalog_database: str | None
    known_query: str | None
    gap_query: str
    checks: tuple[CertificationCheck, ...]
    known_trace: dict[str, Any] = field(default_factory=dict)
    gap_trace: dict[str, Any] = field(default_factory=dict)
    runtime_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "EXCELLENT" if all(item.passed for item in self.checks) else "FAILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repository_root": self.repository_root,
            "catalog_database": self.catalog_database,
            "known_query": self.known_query,
            "gap_query": self.gap_query,
            "status": self.status,
            "checks_executed": len(self.checks),
            "checks_passed": sum(item.passed for item in self.checks),
            "checks_failed": sum(not item.passed for item in self.checks),
            "checks": [item.to_dict() for item in self.checks],
            "known_trace": dict(self.known_trace),
            "gap_trace": dict(self.gap_trace),
            "runtime_snapshot": dict(self.runtime_snapshot),
        }
