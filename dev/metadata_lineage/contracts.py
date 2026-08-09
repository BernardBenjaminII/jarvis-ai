from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MetadataLineageReport:
    status: str
    classification: str
    databases: tuple[dict[str, Any], ...]
    table_profiles: tuple[dict[str, Any], ...]
    join_candidates: tuple[dict[str, Any], ...]
    lineage_paths: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "classification": self.classification,
            "databases": [dict(item) for item in self.databases],
            "table_profiles": [dict(item) for item in self.table_profiles],
            "join_candidates": [dict(item) for item in self.join_candidates],
            "lineage_paths": [dict(item) for item in self.lineage_paths],
            "summary": dict(self.summary),
            "recommendations": list(self.recommendations),
        }
