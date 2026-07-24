"""Immutable claim contracts for Genesis IV-A3.

A claim is a normalized proposition supported, opposed, or contextualized by
an evidence chain. A claim is not a hypothesis, interpretation, decision, or
action.

Claim identity is deterministic and derived exclusively from canonical
constitutional content.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

from .contracts import (
    Metadata,
    ObservationValue,
    normalize_confidence,
    normalize_metadata,
)
from .errors import CognitionValidationError
from .evidence_chain import EvidenceChain
from .normalization import (
    normalize_concept,
    normalize_display_text,
    normalize_identifier_token,
)
from .serialization import canonical_fingerprint


GENESIS_IV_A3_SCHEMA_VERSION = "4.3.0"


class ClaimKind(str, Enum):
    """Constitutional classifications for claims."""

    PROPERTY = "property"
    STATE = "state"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    EXISTENCE = "existence"
    ABSENCE = "absence"
    QUANTITY = "quantity"
    CLASSIFICATION = "classification"


class ClaimPolarity(str, Enum):
    """Whether a claim asserts or denies its proposition."""

    AFFIRMATIVE = "affirmative"
    NEGATIVE = "negative"


class ClaimStatus(str, Enum):
    """Evidence-grounded lifecycle state of a claim."""

    PROPOSED = "proposed"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    INSUFFICIENT = "insufficient"
    REJECTED = "rejected"


class ClaimScope(str, Enum):
    """Scope of applicability declared by the claim."""

    SPECIFIC = "specific"
    LOCAL = "local"
    GENERAL = "general"
    UNIVERSAL = "universal"
    UNKNOWN = "unknown"


def make_claim_id(payload: object) -> str:
    """Create a deterministic claim identifier."""

    return f"cog_claim_{canonical_fingerprint(payload)[:32]}"


def _normalize_identifier_tuple(
    values: Iterable[str],
    *,
    allow_empty: bool,
    field_name: str,
) -> tuple[str, ...]:
    normalized = {
        normalize_display_text(value)
        for value in values
    }

    if not allow_empty and not normalized:
        raise CognitionValidationError(
            f"{field_name} must contain at least one identifier."
        )

    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ClaimPredicate:
    """Canonical subject-predicate-object proposition."""

    subject: str
    predicate: str
    object_value: ObservationValue | None = None
    object_reference_id: str | None = None

    def __post_init__(self) -> None:
        subject = normalize_concept(self.subject)
        predicate = normalize_identifier_token(self.predicate)

        if not subject:
            raise CognitionValidationError(
                "ClaimPredicate.subject may not be empty."
            )

        if not predicate:
            raise CognitionValidationError(
                "ClaimPredicate.predicate may not be empty."
            )

        object_value = self.object_value
        object_reference_id = self.object_reference_id

        if object_value is None and object_reference_id is None:
            raise CognitionValidationError(
                "A claim predicate requires an object value or reference."
            )

        if object_value is not None and object_reference_id is not None:
            raise CognitionValidationError(
                "A claim predicate may not define both object_value and "
                "object_reference_id."
            )

        if object_value is not None and not isinstance(
            object_value,
            ObservationValue,
        ):
            raise CognitionValidationError(
                "ClaimPredicate.object_value must be an ObservationValue."
            )

        if object_reference_id is not None:
            object_reference_id = normalize_display_text(
                object_reference_id
            )

        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "predicate", predicate)
        object.__setattr__(
            self,
            "object_reference_id",
            object_reference_id,
        )

    def identity_payload(self) -> dict[str, object]:
        """Return canonical proposition content."""

        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object_value": self.object_value,
            "object_reference_id": self.object_reference_id,
        }


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    """Immutable evidence-grounded claim."""

    predicate: ClaimPredicate
    evidence_chain: EvidenceChain
    kind: ClaimKind
    polarity: ClaimPolarity = ClaimPolarity.AFFIRMATIVE
    status: ClaimStatus = ClaimStatus.PROPOSED
    scope: ClaimScope = ClaimScope.SPECIFIC
    confidence: Decimal = Decimal("0.5")
    observation_ids: tuple[str, ...] = ()
    description: str | None = None
    metadata: Metadata = ()
    schema_version: str = GENESIS_IV_A3_SCHEMA_VERSION
    claim_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.predicate, ClaimPredicate):
            raise CognitionValidationError(
                "ClaimRecord.predicate must be a ClaimPredicate."
            )

        if not isinstance(self.evidence_chain, EvidenceChain):
            raise CognitionValidationError(
                "ClaimRecord.evidence_chain must be an EvidenceChain."
            )

        for field_name, enum_type in (
            ("kind", ClaimKind),
            ("polarity", ClaimPolarity),
            ("status", ClaimStatus),
            ("scope", ClaimScope),
        ):
            current_value = getattr(self, field_name)

            if isinstance(current_value, enum_type):
                continue

            try:
                object.__setattr__(
                    self,
                    field_name,
                    enum_type(str(current_value)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported {field_name}: {current_value!r}"
                ) from exc

        object.__setattr__(
            self,
            "confidence",
            normalize_confidence(self.confidence),
        )

        observation_ids = _normalize_identifier_tuple(
            self.observation_ids,
            allow_empty=False,
            field_name="observation_ids",
        )
        object.__setattr__(
            self,
            "observation_ids",
            observation_ids,
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

        expected_id = make_claim_id(self.identity_payload())

        if self.claim_id:
            supplied_id = normalize_display_text(self.claim_id)

            if supplied_id != expected_id:
                raise CognitionValidationError(
                    "Claim identifier does not match canonical content."
                )

            object.__setattr__(self, "claim_id", supplied_id)
        else:
            object.__setattr__(self, "claim_id", expected_id)

    def identity_payload(self) -> dict[str, object]:
        """Return content that constitutionally determines claim identity."""

        return {
            "schema_version": self.schema_version,
            "predicate": self.predicate.identity_payload(),
            "evidence_chain_id": self.evidence_chain.chain_id,
            "kind": self.kind.value,
            "polarity": self.polarity.value,
            "status": self.status.value,
            "scope": self.scope.value,
            "confidence": self.confidence,
            "observation_ids": self.observation_ids,
            "description": self.description,
            "metadata": self.metadata,
        }

    @property
    def proposition_key(self) -> tuple[str, str, str]:
        """Return a stable key useful for later relationship discovery."""

        if self.predicate.object_value is not None:
            object_key = canonical_fingerprint(
                self.predicate.object_value
            )
        else:
            object_key = str(
                self.predicate.object_reference_id
            )

        return (
            self.predicate.subject,
            self.predicate.predicate,
            object_key,
        )
