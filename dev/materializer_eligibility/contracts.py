from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class MaterializerEligibilityReport:
    status: str
    classification: str
    implementation: dict[str, Any]
    authority_map: dict[str, Any]
    dispositions: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "classification": self.classification,
            "implementation": dict(self.implementation),
            "authority_map": dict(self.authority_map),
            "dispositions": [dict(item) for item in self.dispositions],
            "summary": dict(self.summary),
            "recommendations": list(self.recommendations),
        }
