from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .contracts import QualifiedEvidence

@dataclass(frozen=True, slots=True)
class QualificationDiagnostic:
    query: str
    source_id: str
    source_path: str
    accepted: bool
    decision: str
    score: dict[str, float]
    explanation: str

    @classmethod
    def from_evidence(cls, query: str, evidence: QualifiedEvidence):
        return cls(query,evidence.candidate.source_id,evidence.candidate.source_path,
                   evidence.accepted,evidence.decision.value,evidence.score.to_dict(),
                   evidence.explanation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query":self.query,"source_id":self.source_id,"source_path":self.source_path,
            "accepted":self.accepted,"decision":self.decision,
            "score":dict(self.score),"explanation":self.explanation,
        }
