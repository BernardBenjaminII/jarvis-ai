"""Structural validation for Genesis IV-A1 cognition contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .contracts import (
    GENESIS_IV_A1_SCHEMA_VERSION,
    Observation,
    ObservationValue,
    SourceReference,
)
from .enums import CognitiveObjectKind, ObservationValueKind
from .errors import (
    CognitionValidationError,
    UnsupportedCognitiveObjectError,
)
from .identifiers import verify_cognition_id


def validate_source_reference(source: SourceReference) -> None:
    """Validate an immutable observation provenance reference."""

    if not isinstance(source, SourceReference):
        raise CognitionValidationError(
            "Expected a SourceReference instance."
        )

    if not source.source_id.strip():
        raise CognitionValidationError(
            "SourceReference source_id must not be empty."
        )

    if source.start_offset is not None:
        if source.end_offset is None:
            raise CognitionValidationError(
                "SourceReference end_offset is required with start_offset."
            )

        if source.end_offset <= source.start_offset:
            raise CognitionValidationError(
                "SourceReference offsets are not ordered."
            )

    if len(source.evidence_ids) != len(set(source.evidence_ids)):
        raise CognitionValidationError(
            "SourceReference evidence IDs must be unique."
        )


def validate_observation_value(value: ObservationValue) -> None:
    """Validate a directly observed value contract."""

    if not isinstance(value, ObservationValue):
        raise CognitionValidationError(
            "Expected an ObservationValue instance."
        )

    if not value.value.strip():
        raise CognitionValidationError(
            "ObservationValue value must not be empty."
        )

    if value.unit is not None and value.kind is not ObservationValueKind.QUANTITY:
        raise CognitionValidationError(
            "Only quantity observations may define units."
        )


def validate_observation(observation: Observation) -> None:
    """Validate a constitutional observation and its deterministic identity."""

    if not isinstance(observation, Observation):
        raise CognitionValidationError(
            "Expected an Observation instance."
        )

    if observation.schema_version != GENESIS_IV_A1_SCHEMA_VERSION:
        raise CognitionValidationError(
            "Unsupported Genesis IV-A1 observation schema version: "
            f"{observation.schema_version!r}"
        )

    if not observation.subject.strip():
        raise CognitionValidationError(
            "Observation subject must not be empty."
        )

    if not observation.predicate.strip():
        raise CognitionValidationError(
            "Observation predicate must not be empty."
        )

    if not isinstance(observation.confidence, Decimal):
        raise CognitionValidationError(
            "Observation confidence must be a Decimal."
        )

    if observation.confidence < Decimal("0") or observation.confidence > Decimal("1"):
        raise CognitionValidationError(
            "Observation confidence must be between 0 and 1 inclusive."
        )

    validate_observation_value(observation.value)
    validate_source_reference(observation.source)

    verify_cognition_id(
        observation.observation_id,
        CognitiveObjectKind.OBSERVATION,
        observation.identity_payload(),
    )


def validate_cognitive_object(value: Any) -> None:
    """Dispatch validation for a supported cognition-domain object."""

    if isinstance(value, Observation):
        validate_observation(value)
        return

    if isinstance(value, ObservationValue):
        validate_observation_value(value)
        return

    if isinstance(value, SourceReference):
        validate_source_reference(value)
        return

    raise UnsupportedCognitiveObjectError(
        f"Unsupported cognition object: {type(value).__name__}"
    )
