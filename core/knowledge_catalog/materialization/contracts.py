from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class MaterializationReport:
    catalog_path: str
    candidates: int
    materialized: int
    unchanged: int
    skipped: int
    failed: int
    chunks_written: int
    failures: tuple[dict[str, str], ...] = ()

    @property
    def status(self) -> str:
        if self.failed and not self.materialized:
            return "failed"
        if self.failed:
            return "partial"
        return "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "catalog_path": self.catalog_path,
            "candidates": self.candidates,
            "materialized": self.materialized,
            "unchanged": self.unchanged,
            "skipped": self.skipped,
            "failed": self.failed,
            "chunks_written": self.chunks_written,
            "failures": list(self.failures),
        }
