"""Canonical vocabulary for the Genesis IV cognition layer."""

from __future__ import annotations

from enum import Enum


class CognitiveObjectKind(str, Enum):
    """Constitutional cognition-object classifications."""

    OBSERVATION = "observation"
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    HYPOTHESIS = "hypothesis"
    INTERPRETATION = "interpretation"
    QUESTION = "question"
    CONTRADICTION = "contradiction"
    EVIDENCE_CHAIN = "evidence_chain"


class ObservationValueKind(str, Enum):
    """Supported representations for directly observed values."""

    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    QUANTITY = "quantity"
    IDENTIFIER = "identifier"
    UNKNOWN = "unknown"


class ObservationPolarity(str, Enum):
    """Whether the source affirms, negates, or qualifies an observation."""

    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"


class ObservationOrigin(str, Enum):
    """How an observation entered the cognition layer."""

    DIRECT_EXTRACTION = "direct_extraction"
    STRUCTURED_INPUT = "structured_input"
    OPERATOR_ENTRY = "operator_entry"


class ConfidenceBand(str, Enum):
    """Human-readable interpretation of a normalized confidence score."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
