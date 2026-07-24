"""Immutable evidence-chain contracts for Genesis IV-A2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

from .contracts import Metadata, normalize_confidence, normalize_metadata
from .errors import CognitionValidationError
from .evidence import EvidenceDirection, EvidenceRecord
from .normalization import normalize_display_text
from .provenance import GENESIS_IV_A2_SCHEMA_VERSION
from .serialization import canonical_fingerprint


class EvidenceChainStatus(str, Enum):
    """Lifecycle state of an immutable evidence chain."""

    OPEN = "open"
    COMPLETE = "complete"
    CONTESTED = "contested"
    INSUFFICIENT = "insufficient"


def make_evidence_chain_id(payload: object) -> str:
    """Create a deterministic evidence-chain identifier."""

    return f"cog_evidence_chain_{canonical_fingerprint(payload)[:32]}"


def _normalize_evidence_records(
    records: Iterable[EvidenceRecord],
) -> tuple[EvidenceRecord, ...]:
    by_id: dict[str, EvidenceRecord] = {}

    for record in records:
        if not isinstance(record, EvidenceRecord):
            raise CognitionValidationError(
                "Evidence chains may contain only EvidenceRecord objects."
            )

        existing = by_id.get(record.evidence_id)

        if existing is not None and existing != record:
            raise CognitionValidationError(
                "Conflicting evidence records share an identifier."
            )

        by_id[record.evidence_id] = record

    if not by_id:
        raise CognitionValidationError(
            "Evidence chains require at least one evidence record."
        )

    return tuple(
        by_id[evidence_id]
        for evidence_id in sorted(by_id)
    )


@dataclass(frozen=True, slots=True)
class EvidenceChain:
    """Immutable ordered set of evidence supporting later cognition."""

    subject_id: str
    evidence: tuple[EvidenceRecord, ...]
    status: EvidenceChainStatus = EvidenceChainStatus.OPEN
    confidence: Decimal = Decimal("0.5")
    description: str | None = None
    metadata: Metadata = ()
    schema_version: str = GENESIS_IV_A2_SCHEMA_VERSION
    chain_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "subject_id",
            normalize_display_text(self.subject_id),
        )
        object.__setattr__(
            self,
            "evidence",
            _normalize_evidence_records(self.evidence),
        )

        if not isinstance(self.status, EvidenceChainStatus):
            try:
                object.__setattr__(
                    self,
                    "status",
                    EvidenceChainStatus(str(self.status)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported evidence-chain status: {self.status!r}"
                ) from exc

        object.__setattr__(
            self,
            "confidence",
            normalize_confidence(self.confidence),
        )

        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                normalize_display_text(self.description),
            )

        object.__setattr__(
            self,
            "metadata",
            normalize_metadata(self.metadata),
        )

        schema_version = normalize_display_text(self.schema_version)
        object.__setattr__(
            self,
            "schema_version",
            schema_version,
        )

        expected_id = make_evidence_chain_id(
            self.identity_payload()
        )

        if self.chain_id:
            supplied_id = normalize_display_text(self.chain_id)

            if supplied_id != expected_id:
                raise CognitionValidationError(
                    "Evidence-chain identifier does not match canonical content."
                )

            object.__setattr__(
                self,
                "chain_id",
                supplied_id,
            )
        else:
            object.__setattr__(
                self,
                "chain_id",
                expected_id,
            )

    def identity_payload(self) -> dict[str, object]:
        """Return content that constitutionally determines identity."""

        return {
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
            "evidence_ids": tuple(
                record.evidence_id
                for record in self.evidence
            ),
            "status": self.status.value,
            "confidence": self.confidence,
            "description": self.description,
            "metadata": self.metadata,
        }

    @property
    def supporting_evidence(self) -> tuple[EvidenceRecord, ...]:
        """Return evidence whose declared direction is supportive."""

        return tuple(
            record
            for record in self.evidence
            if record.direction is EvidenceDirection.SUPPORTS
        )

    @property
    def opposing_evidence(self) -> tuple[EvidenceRecord, ...]:
        """Return evidence whose declared direction is opposing."""

        return tuple(
            record
            for record in self.evidence
            if record.direction is EvidenceDirection.OPPOSES
        )

    @property
    def neutral_evidence(self) -> tuple[EvidenceRecord, ...]:
        """Return evidence whose direction is neutral."""

        return tuple(
            record
            for record in self.evidence
            if record.direction is EvidenceDirection.NEUTRAL
        )

    @property
    def is_contested(self) -> bool:
        """Return whether the chain contains support and opposition."""

        return bool(
            self.supporting_evidence
            and self.opposing_evidence
        )
