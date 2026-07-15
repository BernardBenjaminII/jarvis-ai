"""
Immutable results for provenance-aware acquisition intake.

The intake layer joins:

- durable provenance lookup
- admission evaluation
- provenance recording

It does not commit or roll back transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge_engine.acquisition.admission.models import (
    AdmissionDecision,
)
from knowledge_engine.acquisition.provenance.models import (
    ProvenanceWriteResult,
)


@dataclass(frozen=True, slots=True)
class AcquisitionIntakeResult:
    """Result of evaluating and recording one acquisition candidate."""

    decision: AdmissionDecision
    provenance: ProvenanceWriteResult
    known_checksum_count: int

    def __post_init__(self) -> None:
        if self.known_checksum_count < 0:
            raise ValueError(
                "known_checksum_count must not be negative"
            )

        if (
            self.decision.candidate.provider_id
            != self.provenance.record.provider_id
        ):
            raise ValueError(
                "Decision and provenance provider IDs do not match"
            )

        if (
            self.decision.candidate.source_uri
            != self.provenance.record.source_uri
        ):
            raise ValueError(
                "Decision and provenance source URIs do not match"
            )

        if (
            self.decision.fingerprint
            != self.provenance.history.decision_fingerprint
        ):
            raise ValueError(
                "Decision and provenance fingerprints do not match"
            )

    @property
    def candidate_id(self) -> str:
        return self.provenance.candidate_id

    @property
    def created(self) -> bool:
        return self.provenance.created

    @property
    def sighting_count(self) -> int:
        return self.provenance.sighting_count

    @property
    def action(self) -> str:
        return self.decision.action.value

    @property
    def admitted(self) -> bool:
        return self.decision.accepted

    @property
    def already_known(self) -> bool:
        return (
            "exact_duplicate"
            in tuple(
                evaluation.reason_code
                for evaluation in self.decision.evaluations
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "created": self.created,
            "sighting_count": self.sighting_count,
            "action": self.action,
            "admitted": self.admitted,
            "already_known": self.already_known,
            "known_checksum_count": self.known_checksum_count,
            "decision": self.decision.to_dict(),
            "provenance": self.provenance.record.to_dict(),
            "history_id": self.provenance.history.history_id,
        }


__all__ = [
    "AcquisitionIntakeResult",
]
