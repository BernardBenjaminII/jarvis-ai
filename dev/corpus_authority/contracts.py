from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class CorpusAuthorityReport:
    status: str
    classification: str
    authorities: tuple[dict[str, Any], ...]
    database_comparisons: tuple[dict[str, Any], ...]
    pipeline_stages: tuple[dict[str, Any], ...]
    lineage_edges: tuple[dict[str, Any], ...]
    dropoff: dict[str, Any]
    summary: dict[str, Any]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "classification": self.classification,
            "authorities": [dict(item) for item in self.authorities],
            "database_comparisons": [dict(item) for item in self.database_comparisons],
            "pipeline_stages": [dict(item) for item in self.pipeline_stages],
            "lineage_edges": [dict(item) for item in self.lineage_edges],
            "dropoff": dict(self.dropoff),
            "summary": dict(self.summary),
            "recommendations": list(self.recommendations),
        }
