"""Immutable constitutional contracts for Genesis IV-A1 observations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping

from .enums import (
    CognitiveObjectKind,
    ObservationOrigin,
    ObservationPolarity,
    ObservationValueKind,
)
from .errors import CognitionValidationError
from .identifiers import make_cognition_id
from .serialization import canonical_fingerprint

GENESIS_IV_A1_SCHEMA_VERSION = "4.1.0"

Metadata = tuple[tuple[str, str], ...]


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise CognitionValidationError(f"{field_name} must be a string.")

    normalized = value.strip()

    if not normalized:
        raise CognitionValidationError(f"{field_name} must not be empty.")

    return normalized


def _optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None

    return _required_text(value, field_name)


def normalize_metadata(
    metadata: Mapping[str, str] | Iterable[tuple[str, str]] | None,
) -> Metadata:
    """Normalize metadata into a sorted immutable key-value sequence."""

    if metadata is None:
        return ()

    items = metadata.items() if isinstance(metadata, Mapping) else metadata
    normalized: dict[str, str] = {}

    for raw_key, raw_value in items:
        key = _required_text(raw_key, "metadata key")
        value = _required_text(raw_value, f"metadata[{key!r}]")

        if key in normalized:
            raise CognitionValidationError(
                f"Duplicate metadata key: {key!r}"
            )

        normalized[key] = value

    return tuple(sorted(normalized.items()))


def normalize_confidence(value: Decimal | str | int) -> Decimal:
    """Normalize confidence into an exact decimal from zero through one."""

    if isinstance(value, bool):
        raise CognitionValidationError(
            "Confidence must not be represented as a boolean."
        )

    try:
        confidence = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CognitionValidationError(
            f"Invalid confidence value: {value!r}"
        ) from exc

    if not confidence.is_finite():
        raise CognitionValidationError("Confidence must be finite.")

    if confidence < Decimal("0") or confidence > Decimal("1"):
        raise CognitionValidationError(
            "Confidence must be between 0 and 1 inclusive."
        )

    return confidence.normalize()


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Immutable provenance reference for a directly observed statement."""

    source_id: str
    segment_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    excerpt: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _required_text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "segment_id",
            _optional_text(self.segment_id, "segment_id"),
        )
        object.__setattr__(
            self,
            "excerpt",
            _optional_text(self.excerpt, "excerpt"),
        )

        if not isinstance(self.evidence_ids, tuple):
            object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

        normalized_evidence_ids = tuple(
            _required_text(value, "evidence_id")
            for value in self.evidence_ids
        )

        if len(set(normalized_evidence_ids)) != len(normalized_evidence_ids):
            raise CognitionValidationError(
                "SourceReference evidence_ids must be unique."
            )

        object.__setattr__(
            self,
            "evidence_ids",
            tuple(sorted(normalized_evidence_ids)),
        )

        offsets = (self.start_offset, self.end_offset)

        if (offsets[0] is None) != (offsets[1] is None):
            raise CognitionValidationError(
                "start_offset and end_offset must be supplied together."
            )

        if self.start_offset is not None:
            if isinstance(self.start_offset, bool) or not isinstance(
                self.start_offset,
                int,
            ):
                raise CognitionValidationError(
                    "start_offset must be an integer."
                )

            if isinstance(self.end_offset, bool) or not isinstance(
                self.end_offset,
                int,
            ):
                raise CognitionValidationError(
                    "end_offset must be an integer."
                )

            if self.start_offset < 0:
                raise CognitionValidationError(
                    "start_offset must not be negative."
                )

            if self.end_offset <= self.start_offset:
                raise CognitionValidationError(
                    "end_offset must be greater than start_offset."
                )

    def identity_payload(self) -> dict[str, object]:
        """Return canonical identity-bearing source data."""

        return {
            "source_id": self.source_id,
            "segment_id": self.segment_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "excerpt": self.excerpt,
            "evidence_ids": self.evidence_ids,
        }


@dataclass(frozen=True, slots=True)
class ObservationValue:
    """Immutable object or value directly expressed by source material."""

    kind: ObservationValueKind
    value: str
    normalized_value: str | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ObservationValueKind):
            try:
                object.__setattr__(
                    self,
                    "kind",
                    ObservationValueKind(str(self.kind)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported observation value kind: {self.kind!r}"
                ) from exc

        object.__setattr__(
            self,
            "value",
            _required_text(self.value, "value"),
        )
        object.__setattr__(
            self,
            "normalized_value",
            _optional_text(self.normalized_value, "normalized_value"),
        )
        object.__setattr__(
            self,
            "unit",
            _optional_text(self.unit, "unit"),
        )

        if self.unit is not None and self.kind is not ObservationValueKind.QUANTITY:
            raise CognitionValidationError(
                "A unit may only be attached to a quantity observation."
            )

    def identity_payload(self) -> dict[str, object]:
        """Return canonical identity-bearing value data."""

        return {
            "kind": self.kind,
            "value": self.value,
            "normalized_value": self.normalized_value,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class Observation:
    """Immutable direct observation extracted without inference."""

    observation_id: str
    subject: str
    predicate: str
    value: ObservationValue
    source: SourceReference
    polarity: ObservationPolarity
    origin: ObservationOrigin
    confidence: Decimal
    metadata: Metadata = ()
    schema_version: str = GENESIS_IV_A1_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "subject",
            _required_text(self.subject, "subject"),
        )
        object.__setattr__(
            self,
            "predicate",
            _required_text(self.predicate, "predicate"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _required_text(self.schema_version, "schema_version"),
        )

        if not isinstance(self.value, ObservationValue):
            raise CognitionValidationError(
                "value must be an ObservationValue."
            )

        if not isinstance(self.source, SourceReference):
            raise CognitionValidationError(
                "source must be a SourceReference."
            )

        if not isinstance(self.polarity, ObservationPolarity):
            try:
                object.__setattr__(
                    self,
                    "polarity",
                    ObservationPolarity(str(self.polarity)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported observation polarity: {self.polarity!r}"
                ) from exc

        if not isinstance(self.origin, ObservationOrigin):
            try:
                object.__setattr__(
                    self,
                    "origin",
                    ObservationOrigin(str(self.origin)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported observation origin: {self.origin!r}"
                ) from exc

        object.__setattr__(
            self,
            "confidence",
            normalize_confidence(self.confidence),
        )
        object.__setattr__(
            self,
            "metadata",
            normalize_metadata(self.metadata),
        )

        expected_id = make_cognition_id(
            CognitiveObjectKind.OBSERVATION,
            self.identity_payload(),
        )

        if self.observation_id != expected_id:
            raise CognitionValidationError(
                "observation_id does not match the canonical observation identity. "
                f"Expected {expected_id!r}, received {self.observation_id!r}."
            )

    @classmethod
    def create(
        cls,
        *,
        subject: str,
        predicate: str,
        value: ObservationValue,
        source: SourceReference,
        polarity: ObservationPolarity = ObservationPolarity.AFFIRMED,
        origin: ObservationOrigin = ObservationOrigin.DIRECT_EXTRACTION,
        confidence: Decimal | str | int = Decimal("1"),
        metadata: Mapping[str, str] | Iterable[tuple[str, str]] | None = None,
        schema_version: str = GENESIS_IV_A1_SCHEMA_VERSION,
    ) -> "Observation":
        """Construct an observation with a deterministic canonical identity."""

        normalized_subject = _required_text(subject, "subject")
        normalized_predicate = _required_text(predicate, "predicate")
        normalized_metadata = normalize_metadata(metadata)
        normalized_confidence = normalize_confidence(confidence)
        normalized_schema_version = _required_text(
            schema_version,
            "schema_version",
        )

        if not isinstance(value, ObservationValue):
            raise CognitionValidationError(
                "value must be an ObservationValue."
            )

        if not isinstance(source, SourceReference):
            raise CognitionValidationError(
                "source must be a SourceReference."
            )

        if not isinstance(polarity, ObservationPolarity):
            polarity = ObservationPolarity(str(polarity))

        if not isinstance(origin, ObservationOrigin):
            origin = ObservationOrigin(str(origin))

        identity_payload = cls.build_identity_payload(
            subject=normalized_subject,
            predicate=normalized_predicate,
            value=value,
            source=source,
            polarity=polarity,
            origin=origin,
            schema_version=normalized_schema_version,
        )

        observation_id = make_cognition_id(
            CognitiveObjectKind.OBSERVATION,
            identity_payload,
        )

        return cls(
            observation_id=observation_id,
            subject=normalized_subject,
            predicate=normalized_predicate,
            value=value,
            source=source,
            polarity=polarity,
            origin=origin,
            confidence=normalized_confidence,
            metadata=normalized_metadata,
            schema_version=normalized_schema_version,
        )

    @staticmethod
    def build_identity_payload(
        *,
        subject: str,
        predicate: str,
        value: ObservationValue,
        source: SourceReference,
        polarity: ObservationPolarity,
        origin: ObservationOrigin,
        schema_version: str,
    ) -> dict[str, object]:
        """Build the canonical identity-bearing observation payload."""

        return {
            "kind": CognitiveObjectKind.OBSERVATION,
            "schema_version": schema_version,
            "subject": subject,
            "predicate": predicate,
            "value": value.identity_payload(),
            "source": source.identity_payload(),
            "polarity": polarity,
            "origin": origin,
        }

    def identity_payload(self) -> dict[str, object]:
        """Return the canonical payload that determines this observation's ID."""

        return self.build_identity_payload(
            subject=self.subject,
            predicate=self.predicate,
            value=self.value,
            source=self.source,
            polarity=self.polarity,
            origin=self.origin,
            schema_version=self.schema_version,
        )

    def content_fingerprint(self) -> str:
        """Return the deterministic fingerprint of the full observation."""

        return canonical_fingerprint(self)
