"""Immutable evidence contracts for Genesis IV-A2.

Evidence is source-grounded support or opposition associated with one or more
observations. Evidence is not itself a conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

from .contracts import (
    Metadata,
    Observation,
    normalize_confidence,
    normalize_metadata,
)
from .errors import CognitionValidationError
from .normalization import normalize_display_text
from .provenance import (
    GENESIS_IV_A2_SCHEMA_VERSION,
    ProvenanceRecord,
)
from .serialization import canonical_fingerprint


class EvidenceKind(str, Enum):
    """Constitutional evidence classifications."""

    DIRECT = "direct"
    CORROBORATING = "corroborating"
    CONTRADICTING = "contradicting"
    CONTEXTUAL = "contextual"
    NEGATIVE = "negative"
    EXCLUSIONARY = "exclusionary"


class EvidenceDirection(str, Enum):
    """Direction in which evidence bears on an observation or claim."""

    SUPPORTS = "supports"
    OPPOSES = "opposes"
    NEUTRAL = "neutral"


class EvidenceQuality(str, Enum):
    """Quality classification independent of conclusion truth."""

    UNASSESSED = "unassessed"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    AUTHORITATIVE = "authoritative"


def _normalize_identifier_tuple(
    values: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = {
        normalize_display_text(value)
        for value in values
    }

    if not normalized:
        raise CognitionValidationError(
            f"{field_name} must contain at least one identifier."
        )

    return tuple(sorted(normalized))


def make_evidence_id(payload: object) -> str:
    """Create a deterministic evidence identifier."""

    return f"cog_evidence_{canonical_fingerprint(payload)[:32]}"


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable evidence associated with cognitive objects."""

    observation_ids: tuple[str, ...]
    provenance: ProvenanceRecord
    kind: EvidenceKind
    direction: EvidenceDirection
    quality: EvidenceQuality = EvidenceQuality.UNASSESSED
    confidence: Decimal = Decimal("0.5")
    description: str | None = None
    metadata: Metadata = ()
    schema_version: str = GENESIS_IV_A2_SCHEMA_VERSION
    evidence_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observation_ids",
            _normalize_identifier_tuple(
                self.observation_ids,
                field_name="observation_ids",
            ),
        )

        if not isinstance(self.provenance, ProvenanceRecord):
            raise CognitionValidationError(
                "EvidenceRecord.provenance must be a ProvenanceRecord."
            )

        if not isinstance(self.kind, EvidenceKind):
            try:
                object.__setattr__(
                    self,
                    "kind",
                    EvidenceKind(str(self.kind)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported evidence kind: {self.kind!r}"
                ) from exc

        if not isinstance(self.direction, EvidenceDirection):
            try:
                object.__setattr__(
                    self,
                    "direction",
                    EvidenceDirection(str(self.direction)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported evidence direction: "
                    f"{self.direction!r}"
                ) from exc

        if not isinstance(self.quality, EvidenceQuality):
            try:
                object.__setattr__(
                    self,
                    "quality",
                    EvidenceQuality(str(self.quality)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported evidence quality: {self.quality!r}"
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

        expected_id = make_evidence_id(self.identity_payload())

        if self.evidence_id:
            supplied_id = normalize_display_text(self.evidence_id)

            if supplied_id != expected_id:
                raise CognitionValidationError(
                    "Evidence identifier does not match canonical content."
                )

            object.__setattr__(
                self,
                "evidence_id",
                supplied_id,
            )
        else:
            object.__setattr__(
                self,
                "evidence_id",
                expected_id,
            )

    def identity_payload(self) -> dict[str, object]:
        """Return content that constitutionally determines identity."""

        return {
            "schema_version": self.schema_version,
            "observation_ids": self.observation_ids,
            "provenance_id": self.provenance.provenance_id,
            "kind": self.kind.value,
            "direction": self.direction.value,
            "quality": self.quality.value,
            "confidence": self.confidence,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_observation(
        cls,
        observation: Observation,
        *,
        provenance: ProvenanceRecord,
        kind: EvidenceKind = EvidenceKind.DIRECT,
        direction: EvidenceDirection = EvidenceDirection.SUPPORTS,
        quality: EvidenceQuality = EvidenceQuality.UNASSESSED,
        confidence: Decimal | str | int | None = None,
        description: str | None = None,
        metadata: Metadata = (),
    ) -> "EvidenceRecord":
        """Construct direct evidence for one immutable observation."""

        if not isinstance(observation, Observation):
            raise CognitionValidationError(
                "observation must be an Observation instance."
            )

        resolved_confidence = (
            observation.confidence
            if confidence is None
            else confidence
        )

        return cls(
            observation_ids=(observation.observation_id,),
            provenance=provenance,
            kind=kind,
            direction=direction,
            quality=quality,
            confidence=normalize_confidence(resolved_confidence),
            description=description,
            metadata=metadata,
        )
