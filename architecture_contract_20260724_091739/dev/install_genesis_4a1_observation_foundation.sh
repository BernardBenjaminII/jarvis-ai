#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PACKAGE_ROOT="${PROJECT_ROOT}/core/cognition"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-A1 — COGNITIVE OBSERVATION FOUNDATION"
echo "======================================================================"
echo
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo

if [[ ! -d "${PROJECT_ROOT}/core" ]]; then
    echo "[FAIL] Missing core directory: ${PROJECT_ROOT}/core"
    exit 1
fi

if ! "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    echo "[FAIL] Python interpreter is unavailable: ${PYTHON_BIN}"
    exit 1
fi

mkdir -p "${PACKAGE_ROOT}"

cat > "${PACKAGE_ROOT}/errors.py" <<'PYEOF'
"""Domain exceptions for the Genesis IV cognition layer."""

from __future__ import annotations


class CognitionError(RuntimeError):
    """Base exception for cognition-domain failures."""


class CognitionValidationError(CognitionError, ValueError):
    """Raised when a cognition contract violates its invariants."""


class CognitionIdentifierError(CognitionValidationError):
    """Raised when a deterministic cognition identifier is invalid."""


class CognitionSerializationError(CognitionError):
    """Raised when a cognition object cannot be serialized canonically."""


class UnsupportedCognitiveObjectError(CognitionValidationError):
    """Raised when a validator receives an unsupported cognition object."""
PYEOF

cat > "${PACKAGE_ROOT}/enums.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/serialization.py" <<'PYEOF'
"""Deterministic canonical serialization for cognition objects."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Sequence

from .errors import CognitionSerializationError


def decimal_to_string(value: Decimal) -> str:
    """Return a deterministic non-exponential decimal representation."""

    if not value.is_finite():
        raise CognitionSerializationError(
            "Non-finite decimal values are not canonically serializable."
        )

    normalized = value.normalize()

    if normalized == normalized.to_integral():
        return format(normalized.quantize(Decimal("1")), "f")

    return format(normalized, "f")


def canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-compatible structures."""

    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        raise CognitionSerializationError(
            "Binary floating-point values are forbidden in canonical cognition data. "
            "Use Decimal instead."
        )

    if isinstance(value, Decimal):
        return decimal_to_string(value)

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonicalize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }

    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise CognitionSerializationError(
                    "Canonical mapping keys must be strings."
                )

            converted[key] = canonicalize(item)

        return {
            key: converted[key]
            for key in sorted(converted)
        }

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, set) or isinstance(value, frozenset):
        canonical_items = [canonicalize(item) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ),
        )

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [canonicalize(item) for item in value]

    raise CognitionSerializationError(
        f"Unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize a supported object using the canonical cognition JSON form."""

    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def pretty_json(value: Any) -> str:
    """Serialize a cognition object as stable, human-readable JSON."""

    return (
        json.dumps(
            canonicalize(value),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def canonical_fingerprint(value: Any) -> str:
    """Return a SHA-256 fingerprint of canonical serialized content."""

    encoded = canonical_json(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
PYEOF

cat > "${PACKAGE_ROOT}/identifiers.py" <<'PYEOF'
"""Deterministic identifiers for constitutional cognition objects."""

from __future__ import annotations

import re
from typing import Any

from .enums import CognitiveObjectKind
from .errors import CognitionIdentifierError
from .serialization import canonical_fingerprint

_IDENTIFIER_PATTERN = re.compile(
    r"^cog_(?P<kind>[a-z][a-z0-9_]*)_(?P<digest>[0-9a-f]{32})$"
)


def normalize_kind(kind: CognitiveObjectKind | str) -> str:
    """Normalize and validate a cognitive object kind."""

    value = kind.value if isinstance(kind, CognitiveObjectKind) else str(kind)
    value = value.strip().lower()

    try:
        return CognitiveObjectKind(value).value
    except ValueError as exc:
        raise CognitionIdentifierError(
            f"Unsupported cognitive object kind: {value!r}"
        ) from exc


def make_cognition_id(
    kind: CognitiveObjectKind | str,
    identity_payload: Any,
) -> str:
    """Create a deterministic cognition identifier from canonical identity data."""

    normalized_kind = normalize_kind(kind)
    digest = canonical_fingerprint(identity_payload)[:32]
    return f"cog_{normalized_kind}_{digest}"


def parse_cognition_id(identifier: str) -> tuple[CognitiveObjectKind, str]:
    """Parse and validate a cognition identifier."""

    if not isinstance(identifier, str):
        raise CognitionIdentifierError("Cognition identifiers must be strings.")

    match = _IDENTIFIER_PATTERN.fullmatch(identifier)

    if match is None:
        raise CognitionIdentifierError(
            f"Invalid cognition identifier: {identifier!r}"
        )

    raw_kind = match.group("kind")

    try:
        kind = CognitiveObjectKind(raw_kind)
    except ValueError as exc:
        raise CognitionIdentifierError(
            f"Identifier contains unsupported cognition kind: {raw_kind!r}"
        ) from exc

    return kind, match.group("digest")


def validate_cognition_id(
    identifier: str,
    expected_kind: CognitiveObjectKind | str | None = None,
) -> None:
    """Validate an identifier and optionally enforce its object kind."""

    actual_kind, _ = parse_cognition_id(identifier)

    if expected_kind is None:
        return

    normalized_expected = CognitiveObjectKind(normalize_kind(expected_kind))

    if actual_kind is not normalized_expected:
        raise CognitionIdentifierError(
            f"Expected {normalized_expected.value!r} identifier, "
            f"received {actual_kind.value!r}."
        )


def verify_cognition_id(
    identifier: str,
    kind: CognitiveObjectKind | str,
    identity_payload: Any,
) -> None:
    """Verify that an identifier matches its canonical identity payload."""

    expected = make_cognition_id(kind, identity_payload)

    if identifier != expected:
        raise CognitionIdentifierError(
            f"Identifier does not match canonical identity. "
            f"Expected {expected!r}, received {identifier!r}."
        )
PYEOF

cat > "${PACKAGE_ROOT}/contracts.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/validation.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/__init__.py" <<'PYEOF'
"""Genesis IV cognition-domain public API.

The cognition layer transforms represented knowledge into deterministic,
immutable cognitive objects without performing planning or execution.
"""

from .contracts import (
    GENESIS_IV_A1_SCHEMA_VERSION,
    Metadata,
    Observation,
    ObservationValue,
    SourceReference,
    normalize_confidence,
    normalize_metadata,
)
from .enums import (
    CognitiveObjectKind,
    ConfidenceBand,
    ObservationOrigin,
    ObservationPolarity,
    ObservationValueKind,
)
from .errors import (
    CognitionError,
    CognitionIdentifierError,
    CognitionSerializationError,
    CognitionValidationError,
    UnsupportedCognitiveObjectError,
)
from .identifiers import (
    make_cognition_id,
    normalize_kind,
    parse_cognition_id,
    validate_cognition_id,
    verify_cognition_id,
)
from .serialization import (
    canonical_fingerprint,
    canonical_json,
    canonicalize,
    decimal_to_string,
    pretty_json,
)
from .validation import (
    validate_cognitive_object,
    validate_observation,
    validate_observation_value,
    validate_source_reference,
)

__all__ = [
    "GENESIS_IV_A1_SCHEMA_VERSION",
    "Metadata",
    "Observation",
    "ObservationValue",
    "SourceReference",
    "CognitiveObjectKind",
    "ConfidenceBand",
    "ObservationOrigin",
    "ObservationPolarity",
    "ObservationValueKind",
    "CognitionError",
    "CognitionIdentifierError",
    "CognitionSerializationError",
    "CognitionValidationError",
    "UnsupportedCognitiveObjectError",
    "canonical_fingerprint",
    "canonical_json",
    "canonicalize",
    "decimal_to_string",
    "make_cognition_id",
    "normalize_confidence",
    "normalize_kind",
    "normalize_metadata",
    "parse_cognition_id",
    "pretty_json",
    "validate_cognition_id",
    "validate_cognitive_object",
    "validate_observation",
    "validate_observation_value",
    "validate_source_reference",
    "verify_cognition_id",
]
PYEOF

echo "[PASS] Genesis IV-A1 cognition package files installed"

echo
echo "Compiling cognition package..."
"${PYTHON_BIN}" -m compileall -q "${PACKAGE_ROOT}"
echo "[PASS] Cognition package compilation"

echo
echo "Running public import smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from decimal import Decimal
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
    Observation,
    ObservationOrigin,
    ObservationPolarity,
    ObservationValue,
    ObservationValueKind,
    SourceReference,
    canonical_json,
    validate_observation,
)

source = SourceReference(
    source_id="document:test-battery-report",
    segment_id="segment-0001",
    start_offset=0,
    end_offset=29,
    excerpt="The battery voltage is 10.2 V.",
    evidence_ids=("ev_test_battery_voltage",),
)

value = ObservationValue(
    kind=ObservationValueKind.QUANTITY,
    value="10.2",
    normalized_value="10.2",
    unit="V",
)

first = Observation.create(
    subject="battery",
    predicate="voltage",
    value=value,
    source=source,
    polarity=ObservationPolarity.AFFIRMED,
    origin=ObservationOrigin.DIRECT_EXTRACTION,
    confidence=Decimal("0.98"),
    metadata={"extractor": "genesis-iv-a1-smoke"},
)

second = Observation.create(
    subject="battery",
    predicate="voltage",
    value=value,
    source=source,
    polarity=ObservationPolarity.AFFIRMED,
    origin=ObservationOrigin.DIRECT_EXTRACTION,
    confidence=Decimal("0.98"),
    metadata={"extractor": "genesis-iv-a1-smoke"},
)

validate_observation(first)
validate_observation(second)

assert first == second
assert first.observation_id == second.observation_id
assert canonical_json(first) == canonical_json(second)

print(f"[PASS] Observation ID: {first.observation_id}")
print(f"[PASS] Fingerprint  : {first.content_fingerprint()}")
print("[PASS] Deterministic observation smoke test")
PYEOF

echo
echo "Running immutability smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import ObservationValue, ObservationValueKind

value = ObservationValue(
    kind=ObservationValueKind.TEXT,
    value="operational",
)

try:
    value.value = "modified"
except FrozenInstanceError:
    print("[PASS] Observation contracts are immutable")
else:
    raise SystemExit("[FAIL] ObservationValue mutation was permitted")
PYEOF

echo
echo "======================================================================"
echo "GENESIS IV-A1 PACKAGE 1A INSTALLATION COMPLETE"
echo "======================================================================"
echo
echo "Installed:"
echo "  core/cognition/__init__.py"
echo "  core/cognition/contracts.py"
echo "  core/cognition/enums.py"
echo "  core/cognition/errors.py"
echo "  core/cognition/identifiers.py"
echo "  core/cognition/serialization.py"
echo "  core/cognition/validation.py"
echo
echo "Overall status: EXCELLENT"
echo
