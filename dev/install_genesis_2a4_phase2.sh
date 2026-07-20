#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

EVIDENCE_DIR="core/reasoning/evidence"
TEST_FILE="tests/test_genesis_2a4_evidence_contracts.py"
VERIFY_FILE="dev/verify_genesis_2a4.sh"

mkdir -p "$EVIDENCE_DIR"
mkdir -p tests
mkdir -p dev

cat > "$EVIDENCE_DIR/errors.py" <<'EOF'
"""Domain exceptions for the Genesis II-A4 Evidence model."""

from __future__ import annotations


class EvidenceError(Exception):
    """Base exception for canonical Evidence domain failures."""


class EvidenceValidationError(EvidenceError, ValueError):
    """Raised when an Evidence contract violates a constitutional invariant."""


class EvidenceIdentityError(EvidenceValidationError):
    """Raised when a canonical Evidence identifier is malformed or inconsistent."""


class EvidenceSerializationError(EvidenceError):
    """Raised when a value cannot be canonically serialized."""


class EvidenceUncertaintyError(EvidenceValidationError):
    """Raised when an uncertainty representation is structurally invalid."""


class EvidenceTemporalError(EvidenceValidationError):
    """Raised when Evidence temporal metadata is invalid."""


class EvidenceRelationshipError(EvidenceValidationError):
    """Raised when an Evidence relationship violates its contract."""
EOF

cat > "$EVIDENCE_DIR/enums.py" <<'EOF'
"""Canonical vocabularies for Genesis II-A4 Evidence contracts."""

from __future__ import annotations

from enum import Enum


class StableStringEnum(str, Enum):
    """String-valued enum with stable serialization behavior."""

    def __str__(self) -> str:
        return self.value


class EvidenceSourceType(StableStringEnum):
    """Canonical categories describing where Evidence originated."""

    USER = "user"
    DOCUMENT = "document"
    DATABASE = "database"
    MEMORY = "memory"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    SENSOR = "sensor"
    TOOL = "tool"
    NETWORK_SERVICE = "network_service"
    ANALYST = "analyst"
    MODEL = "model"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class EvidenceModality(StableStringEnum):
    """Epistemic modality of Evidence-bearing content."""

    OBSERVATIONAL = "observational"
    TESTIMONIAL = "testimonial"
    DOCUMENTARY = "documentary"
    INFERENTIAL = "inferential"
    CAUSAL = "causal"
    INTERVENTIONAL = "interventional"
    COUNTERFACTUAL = "counterfactual"
    PREDICTIVE = "predictive"
    NORMATIVE = "normative"
    PROCEDURAL = "procedural"


class EvidenceStatus(StableStringEnum):
    """Non-destructive standing of a canonical Evidence record."""

    ACTIVE = "active"
    QUALIFIED = "qualified"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    INVALIDATED = "invalidated"


class EvidenceRelationshipType(StableStringEnum):
    """Typed, directional relationships between Evidence records."""

    DERIVED_FROM = "derived_from"
    CORROBORATES = "corroborates"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    RETRACTS = "retracts"
    CORRECTS = "corrects"
    QUALIFIES = "qualifies"
    INVALIDATES = "invalidates"
    DEPENDS_ON = "depends_on"
    EXPLAINS = "explains"
    OBSERVED_DURING = "observed_during"
    SAME_ORIGIN_AS = "same_origin_as"


class UncertaintyKind(StableStringEnum):
    """Supported uncertainty representation families."""

    UNKNOWN = "unknown"
    QUALITATIVE = "qualitative"
    PROBABILITY = "probability"
    INTERVAL = "interval"
    LIKELIHOOD = "likelihood"
    BELIEF_FUNCTION = "belief_function"


class AssessmentMethod(StableStringEnum):
    """Method family used to produce an Evidence assessment."""

    HUMAN_REVIEW = "human_review"
    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    PROBABILISTIC = "probabilistic"
    ARGUMENTATIVE = "argumentative"
    CAUSAL = "causal"
    MODEL_ASSISTED = "model_assisted"
    UNSPECIFIED = "unspecified"


class ClassificationLevel(StableStringEnum):
    """Sensitivity classification associated with Evidence content."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    COMPARTMENTED = "compartmented"
    PERSONALLY_SENSITIVE = "personally_sensitive"
    LEGALLY_PROTECTED = "legally_protected"
    OPERATIONALLY_SENSITIVE = "operationally_sensitive"
EOF

cat > "$EVIDENCE_DIR/validation.py" <<'EOF'
"""Structural validation helpers for canonical Evidence contracts."""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Iterable, TypeVar

from .errors import EvidenceTemporalError, EvidenceValidationError

_IDENTIFIER_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9._:/-]*$")
_LANGUAGE_TAG = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_MEDIA_TYPE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/"
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$"
)

T = TypeVar("T")


def normalize_text(value: str, *, field_name: str, allow_empty: bool = False) -> str:
    """Return deterministic Unicode-normalized text."""

    if not isinstance(value, str):
        raise EvidenceValidationError(f"{field_name} must be a string")

    normalized = unicodedata.normalize("NFC", value).strip()

    if not allow_empty and not normalized:
        raise EvidenceValidationError(f"{field_name} must not be empty")

    return normalized


def normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    """Normalize optional text, preserving ``None``."""

    if value is None:
        return None
    return normalize_text(value, field_name=field_name)


def validate_identifier_component(value: str, *, field_name: str) -> str:
    """Validate a stable human-readable identifier component."""

    normalized = normalize_text(value, field_name=field_name).lower()
    if not _IDENTIFIER_COMPONENT.fullmatch(normalized):
        raise EvidenceValidationError(
            f"{field_name} contains unsupported identifier characters"
        )
    return normalized


def validate_language_tag(value: str | None) -> str | None:
    """Validate an optional BCP-47-style language tag."""

    if value is None:
        return None

    normalized = normalize_text(value, field_name="language")
    if not _LANGUAGE_TAG.fullmatch(normalized):
        raise EvidenceValidationError("language is not a valid language tag")
    return normalized


def validate_media_type(value: str) -> str:
    """Validate and normalize an Internet media type."""

    normalized = normalize_text(value, field_name="media_type").lower()
    if not _MEDIA_TYPE.fullmatch(normalized):
        raise EvidenceValidationError("media_type is not a valid media type")
    return normalized


def validate_aware_datetime(
    value: datetime | None,
    *,
    field_name: str,
    required: bool = False,
) -> datetime | None:
    """Require timezone-aware datetimes for deterministic temporal meaning."""

    if value is None:
        if required:
            raise EvidenceTemporalError(f"{field_name} is required")
        return None

    if not isinstance(value, datetime):
        raise EvidenceTemporalError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceTemporalError(f"{field_name} must be timezone-aware")

    return value


def validate_unit_decimal(
    value: Decimal | int | str | None,
    *,
    field_name: str,
    required: bool = False,
) -> Decimal | None:
    """Validate a finite Decimal in the inclusive range [0, 1]."""

    if value is None:
        if required:
            raise EvidenceValidationError(f"{field_name} is required")
        return None

    if isinstance(value, bool) or isinstance(value, float):
        raise EvidenceValidationError(
            f"{field_name} must use Decimal, int, or decimal string input"
        )

    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(value)
    except Exception as exc:
        raise EvidenceValidationError(f"{field_name} is not a valid decimal") from exc

    if not decimal_value.is_finite():
        raise EvidenceValidationError(f"{field_name} must be finite")

    if decimal_value < Decimal("0") or decimal_value > Decimal("1"):
        raise EvidenceValidationError(f"{field_name} must be between 0 and 1")

    return decimal_value.normalize()


def validate_nonnegative_decimal(
    value: Decimal | int | str | None,
    *,
    field_name: str,
    required: bool = False,
) -> Decimal | None:
    """Validate a finite non-negative Decimal."""

    if value is None:
        if required:
            raise EvidenceValidationError(f"{field_name} is required")
        return None

    if isinstance(value, bool) or isinstance(value, float):
        raise EvidenceValidationError(
            f"{field_name} must use Decimal, int, or decimal string input"
        )

    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(value)
    except Exception as exc:
        raise EvidenceValidationError(f"{field_name} is not a valid decimal") from exc

    if not decimal_value.is_finite() or decimal_value < Decimal("0"):
        raise EvidenceValidationError(
            f"{field_name} must be finite and non-negative"
        )

    return decimal_value.normalize()


def normalize_string_tuple(
    values: Iterable[str],
    *,
    field_name: str,
    sort_values: bool = False,
    unique: bool = True,
) -> tuple[str, ...]:
    """Normalize a deterministic tuple of strings."""

    normalized = tuple(
        normalize_text(value, field_name=field_name)
        for value in values
    )

    if unique and len(set(normalized)) != len(normalized):
        raise EvidenceValidationError(f"{field_name} must not contain duplicates")

    if sort_values:
        return tuple(sorted(normalized))

    return normalized


def normalize_key_value_pairs(
    pairs: Iterable[tuple[str, str]],
    *,
    field_name: str,
) -> tuple[tuple[str, str], ...]:
    """Normalize immutable metadata pairs into deterministic key order."""

    normalized: list[tuple[str, str]] = []
    observed_keys: set[str] = set()

    for key, value in pairs:
        normalized_key = validate_identifier_component(
            key,
            field_name=f"{field_name}.key",
        )
        normalized_value = normalize_text(
            value,
            field_name=f"{field_name}.{normalized_key}",
            allow_empty=True,
        )

        if normalized_key in observed_keys:
            raise EvidenceValidationError(
                f"{field_name} contains duplicate key {normalized_key!r}"
            )

        observed_keys.add(normalized_key)
        normalized.append((normalized_key, normalized_value))

    return tuple(sorted(normalized, key=lambda item: item[0]))


def require_nonnegative_integer(value: int, *, field_name: str) -> int:
    """Require a non-negative integer excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceValidationError(
            f"{field_name} must be a non-negative integer"
        )
    return value
EOF

cat > "$EVIDENCE_DIR/serialization.py" <<'EOF'
"""Deterministic canonical serialization for Genesis II-A4 contracts."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from typing import Any

from .errors import EvidenceSerializationError


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise EvidenceSerializationError("non-finite Decimal values are unsupported")

    normalized = value.normalize()

    if normalized == 0:
        return "0"

    rendered = format(normalized, "f")

    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")

    return rendered


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceSerializationError(
            "canonical datetime values must be timezone-aware"
        )

    utc_value = value.astimezone(timezone.utc)
    rendered = utc_value.isoformat(timespec="microseconds")
    return rendered.replace("+00:00", "Z")


def to_canonical_primitive(value: Any) -> Any:
    """Convert supported values into deterministic JSON primitives."""

    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        raise EvidenceSerializationError(
            "floating-point values are prohibited in canonical Evidence serialization"
        )

    if isinstance(value, Decimal):
        return {"$decimal": _canonical_decimal(value)}

    if isinstance(value, datetime):
        return {"$datetime": _canonical_datetime(value)}

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "canonical_value") and callable(value.canonical_value):
        return value.canonical_value()

    if is_dataclass(value):
        return {
            field.name: to_canonical_primitive(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, tuple):
        return [to_canonical_primitive(item) for item in value]

    if isinstance(value, list):
        return [to_canonical_primitive(item) for item in value]

    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise EvidenceSerializationError(
                "canonical mappings require string keys"
            )

        return {
            key: to_canonical_primitive(value[key])
            for key in sorted(value)
        }

    raise EvidenceSerializationError(
        f"unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize a value to canonical compact UTF-8 JSON text."""

    primitive = to_canonical_primitive(value)

    return json.dumps(
        primitive,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    """Serialize a value to canonical UTF-8 bytes."""

    return canonical_json(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 digest of canonical serialization."""

    return sha256(canonical_bytes(value)).hexdigest()
EOF

cat > "$EVIDENCE_DIR/identifiers.py" <<'EOF'
"""Deterministic identifiers for Genesis II-A4 Evidence contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from .errors import EvidenceIdentityError
from .serialization import canonical_sha256

_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")

IdentifierT = TypeVar("IdentifierT", bound="CanonicalEvidenceIdentifier")


@dataclass(frozen=True, slots=True, order=True)
class CanonicalEvidenceIdentifier:
    """Base deterministic identifier represented as ``prefix:sha256``."""

    value: str

    PREFIX: ClassVar[str] = "evidence-id"

    def __post_init__(self) -> None:
        expected_prefix = f"{self.PREFIX}:"

        if not isinstance(self.value, str):
            raise EvidenceIdentityError("identifier value must be a string")

        if not self.value.startswith(expected_prefix):
            raise EvidenceIdentityError(
                f"identifier must begin with {expected_prefix!r}"
            )

        digest = self.value[len(expected_prefix):]

        if not _HEX_DIGEST.fullmatch(digest):
            raise EvidenceIdentityError(
                "identifier digest must be 64 lowercase hexadecimal characters"
            )

    @classmethod
    def from_payload(
        cls: type[IdentifierT],
        payload: Any,
        *,
        identity_version: str = "1",
    ) -> IdentifierT:
        """Create an identifier from canonical payload content."""

        digest = canonical_sha256(
            {
                "identity_type": cls.PREFIX,
                "identity_version": identity_version,
                "payload": payload,
            }
        )
        return cls(f"{cls.PREFIX}:{digest}")

    @classmethod
    def parse(cls: type[IdentifierT], value: str) -> IdentifierT:
        return cls(value)

    def canonical_value(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class EvidenceContentId(CanonicalEvidenceIdentifier):
    """Identity of normalized Evidence content."""

    PREFIX: ClassVar[str] = "evidence-content"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceId(CanonicalEvidenceIdentifier):
    """Identity of a canonical Evidence record."""

    PREFIX: ClassVar[str] = "evidence"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceAssessmentId(CanonicalEvidenceIdentifier):
    """Identity of a contextual Evidence assessment."""

    PREFIX: ClassVar[str] = "evidence-assessment"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceStatusEventId(CanonicalEvidenceIdentifier):
    """Identity of an append-only Evidence standing event."""

    PREFIX: ClassVar[str] = "evidence-status-event"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceRelationshipId(CanonicalEvidenceIdentifier):
    """Identity of a typed Evidence relationship."""

    PREFIX: ClassVar[str] = "evidence-relationship"
EOF

cat > "$EVIDENCE_DIR/contracts.py" <<'EOF'
"""Immutable constitutional contracts for Genesis II-A4 Evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from .enums import (
    AssessmentMethod,
    ClassificationLevel,
    EvidenceModality,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatus,
    UncertaintyKind,
)
from .errors import (
    EvidenceRelationshipError,
    EvidenceTemporalError,
    EvidenceUncertaintyError,
    EvidenceValidationError,
)
from .identifiers import (
    EvidenceAssessmentId,
    EvidenceContentId,
    EvidenceId,
    EvidenceRelationshipId,
    EvidenceStatusEventId,
)
from .validation import (
    normalize_key_value_pairs,
    normalize_optional_text,
    normalize_string_tuple,
    normalize_text,
    require_nonnegative_integer,
    validate_aware_datetime,
    validate_language_tag,
    validate_media_type,
    validate_nonnegative_decimal,
    validate_unit_decimal,
)


@dataclass(frozen=True, slots=True)
class EvidenceContent:
    """Normalized information-bearing content admitted as Evidence."""

    statement: str
    media_type: str = "text/plain"
    language: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "statement",
            normalize_text(self.statement, field_name="statement"),
        )
        object.__setattr__(
            self,
            "media_type",
            validate_media_type(self.media_type),
        )
        object.__setattr__(
            self,
            "language",
            validate_language_tag(self.language),
        )
        object.__setattr__(
            self,
            "attributes",
            normalize_key_value_pairs(
                self.attributes,
                field_name="attributes",
            ),
        )

    @property
    def content_id(self) -> EvidenceContentId:
        """Return deterministic content identity."""

        return EvidenceContentId.from_payload(self)


@dataclass(frozen=True, slots=True)
class EvidenceOrigin:
    """Origin and source-dependence metadata for Evidence."""

    source_type: EvidenceSourceType
    source_id: str
    immediate_source_id: str | None = None
    origin_id: str | None = None
    source_family_id: str | None = None
    collection_event_id: str | None = None
    dependency_group_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, EvidenceSourceType):
            raise EvidenceValidationError(
                "source_type must be an EvidenceSourceType"
            )

        object.__setattr__(
            self,
            "source_id",
            normalize_text(self.source_id, field_name="source_id"),
        )
        object.__setattr__(
            self,
            "immediate_source_id",
            normalize_optional_text(
                self.immediate_source_id,
                field_name="immediate_source_id",
            ),
        )
        object.__setattr__(
            self,
            "origin_id",
            normalize_optional_text(self.origin_id, field_name="origin_id"),
        )
        object.__setattr__(
            self,
            "source_family_id",
            normalize_optional_text(
                self.source_family_id,
                field_name="source_family_id",
            ),
        )
        object.__setattr__(
            self,
            "collection_event_id",
            normalize_optional_text(
                self.collection_event_id,
                field_name="collection_event_id",
            ),
        )
        object.__setattr__(
            self,
            "dependency_group_ids",
            normalize_string_tuple(
                self.dependency_group_ids,
                field_name="dependency_group_ids",
                sort_values=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceProvenanceStep:
    """One immutable transformation or custody step."""

    sequence: int
    actor: str
    mechanism: str
    input_ids: tuple[str, ...] = ()
    transformation: str | None = None
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(self.sequence, field_name="sequence"),
        )
        object.__setattr__(
            self,
            "actor",
            normalize_text(self.actor, field_name="actor"),
        )
        object.__setattr__(
            self,
            "mechanism",
            normalize_text(self.mechanism, field_name="mechanism"),
        )
        object.__setattr__(
            self,
            "input_ids",
            normalize_string_tuple(
                self.input_ids,
                field_name="input_ids",
                sort_values=True,
            ),
        )
        object.__setattr__(
            self,
            "transformation",
            normalize_optional_text(
                self.transformation,
                field_name="transformation",
            ),
        )
        object.__setattr__(
            self,
            "fingerprint",
            normalize_optional_text(
                self.fingerprint,
                field_name="fingerprint",
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Ordered append-safe provenance chain."""

    steps: tuple[EvidenceProvenanceStep, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise EvidenceValidationError(
                "provenance must contain at least one step"
            )

        sequences = tuple(step.sequence for step in self.steps)
        expected = tuple(range(len(self.steps)))

        if sequences != expected:
            raise EvidenceValidationError(
                "provenance sequences must be contiguous and begin at zero"
            )


@dataclass(frozen=True, slots=True)
class EvidenceTemporalScope:
    """Temporal metadata independent from Evidence identity creation."""

    recorded_at: datetime
    observed_at: datetime | None = None
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recorded_at",
            validate_aware_datetime(
                self.recorded_at,
                field_name="recorded_at",
                required=True,
            ),
        )

        for field_name in (
            "observed_at",
            "published_at",
            "valid_from",
            "valid_until",
        ):
            object.__setattr__(
                self,
                field_name,
                validate_aware_datetime(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise EvidenceTemporalError(
                "valid_until must not precede valid_from"
            )


@dataclass(frozen=True, slots=True)
class BeliefMass:
    """One focal-set mass used by a belief-function representation."""

    focal_set: tuple[str, ...]
    mass: Decimal

    def __post_init__(self) -> None:
        normalized_focal_set = normalize_string_tuple(
            self.focal_set,
            field_name="focal_set",
            sort_values=True,
        )

        if not normalized_focal_set:
            raise EvidenceUncertaintyError(
                "belief focal_set must not be empty"
            )

        object.__setattr__(self, "focal_set", normalized_focal_set)
        object.__setattr__(
            self,
            "mass",
            validate_unit_decimal(
                self.mass,
                field_name="mass",
                required=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceUncertainty:
    """Typed uncertainty representation without a universal calculus."""

    kind: UncertaintyKind
    qualitative_label: str | None = None
    probability: Decimal | None = None
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    likelihood: Decimal | None = None
    belief_masses: tuple[BeliefMass, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, UncertaintyKind):
            raise EvidenceUncertaintyError(
                "kind must be an UncertaintyKind"
            )

        object.__setattr__(
            self,
            "qualitative_label",
            normalize_optional_text(
                self.qualitative_label,
                field_name="qualitative_label",
            ),
        )
        object.__setattr__(
            self,
            "probability",
            validate_unit_decimal(
                self.probability,
                field_name="probability",
            ),
        )
        object.__setattr__(
            self,
            "lower_bound",
            validate_unit_decimal(
                self.lower_bound,
                field_name="lower_bound",
            ),
        )
        object.__setattr__(
            self,
            "upper_bound",
            validate_unit_decimal(
                self.upper_bound,
                field_name="upper_bound",
            ),
        )
        object.__setattr__(
            self,
            "likelihood",
            validate_nonnegative_decimal(
                self.likelihood,
                field_name="likelihood",
            ),
        )

        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.lower_bound > self.upper_bound
        ):
            raise EvidenceUncertaintyError(
                "lower_bound must not exceed upper_bound"
            )

        self._validate_kind_contract()

    def _validate_kind_contract(self) -> None:
        populated = {
            "qualitative_label": self.qualitative_label is not None,
            "probability": self.probability is not None,
            "interval": (
                self.lower_bound is not None or self.upper_bound is not None
            ),
            "likelihood": self.likelihood is not None,
            "belief_masses": bool(self.belief_masses),
        }

        if self.kind is UncertaintyKind.UNKNOWN:
            if any(populated.values()):
                raise EvidenceUncertaintyError(
                    "UNKNOWN uncertainty must not contain quantified values"
                )
            return

        if self.kind is UncertaintyKind.QUALITATIVE:
            if self.qualitative_label is None:
                raise EvidenceUncertaintyError(
                    "QUALITATIVE uncertainty requires qualitative_label"
                )
            if any(
                populated[name]
                for name in (
                    "probability",
                    "interval",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "QUALITATIVE uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.PROBABILITY:
            if self.probability is None:
                raise EvidenceUncertaintyError(
                    "PROBABILITY uncertainty requires probability"
                )
            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "interval",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "PROBABILITY uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.INTERVAL:
            if self.lower_bound is None or self.upper_bound is None:
                raise EvidenceUncertaintyError(
                    "INTERVAL uncertainty requires both bounds"
                )
            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "INTERVAL uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.LIKELIHOOD:
            if self.likelihood is None:
                raise EvidenceUncertaintyError(
                    "LIKELIHOOD uncertainty requires likelihood"
                )
            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "interval",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "LIKELIHOOD uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.BELIEF_FUNCTION:
            if not self.belief_masses:
                raise EvidenceUncertaintyError(
                    "BELIEF_FUNCTION uncertainty requires belief_masses"
                )

            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "interval",
                    "likelihood",
                )
            ):
                raise EvidenceUncertaintyError(
                    "BELIEF_FUNCTION uncertainty contains incompatible values"
                )

            total = sum(
                (belief_mass.mass for belief_mass in self.belief_masses),
                start=Decimal("0"),
            )

            if total != Decimal("1"):
                raise EvidenceUncertaintyError(
                    "belief-function masses must sum exactly to 1"
                )


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    """Typed directional relationship between Evidence records."""

    relationship_id: EvidenceRelationshipId
    source_evidence_id: EvidenceId
    target_evidence_id: EvidenceId
    relationship_type: EvidenceRelationshipType
    rationale: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.relationship_id, EvidenceRelationshipId):
            raise EvidenceRelationshipError(
                "relationship_id must be an EvidenceRelationshipId"
            )
        if not isinstance(self.source_evidence_id, EvidenceId):
            raise EvidenceRelationshipError(
                "source_evidence_id must be an EvidenceId"
            )
        if not isinstance(self.target_evidence_id, EvidenceId):
            raise EvidenceRelationshipError(
                "target_evidence_id must be an EvidenceId"
            )
        if self.source_evidence_id == self.target_evidence_id:
            raise EvidenceRelationshipError(
                "an Evidence relationship cannot target itself"
            )
        if not isinstance(
            self.relationship_type,
            EvidenceRelationshipType,
        ):
            raise EvidenceRelationshipError(
                "relationship_type must be an EvidenceRelationshipType"
            )

        object.__setattr__(
            self,
            "rationale",
            normalize_optional_text(self.rationale, field_name="rationale"),
        )
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(self.sequence, field_name="sequence"),
        )

    @classmethod
    def create(
        cls,
        *,
        source_evidence_id: EvidenceId,
        target_evidence_id: EvidenceId,
        relationship_type: EvidenceRelationshipType,
        rationale: str | None = None,
        sequence: int = 0,
    ) -> "EvidenceRelationship":
        payload = {
            "source_evidence_id": source_evidence_id,
            "target_evidence_id": target_evidence_id,
            "relationship_type": relationship_type,
            "rationale": rationale,
            "sequence": sequence,
        }
        return cls(
            relationship_id=EvidenceRelationshipId.from_payload(payload),
            source_evidence_id=source_evidence_id,
            target_evidence_id=target_evidence_id,
            relationship_type=relationship_type,
            rationale=rationale,
            sequence=sequence,
        )


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable historical Evidence record."""

    evidence_id: EvidenceId
    content: EvidenceContent
    origin: EvidenceOrigin
    provenance: EvidenceProvenance
    temporal_scope: EvidenceTemporalScope
    uncertainty: EvidenceUncertainty
    modality: EvidenceModality
    status: EvidenceStatus = EvidenceStatus.ACTIVE
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    tags: tuple[str, ...] = ()
    parent_evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )
        if not isinstance(self.content, EvidenceContent):
            raise EvidenceValidationError(
                "content must be an EvidenceContent"
            )
        if not isinstance(self.origin, EvidenceOrigin):
            raise EvidenceValidationError(
                "origin must be an EvidenceOrigin"
            )
        if not isinstance(self.provenance, EvidenceProvenance):
            raise EvidenceValidationError(
                "provenance must be an EvidenceProvenance"
            )
        if not isinstance(self.temporal_scope, EvidenceTemporalScope):
            raise EvidenceValidationError(
                "temporal_scope must be an EvidenceTemporalScope"
            )
        if not isinstance(self.uncertainty, EvidenceUncertainty):
            raise EvidenceValidationError(
                "uncertainty must be an EvidenceUncertainty"
            )
        if not isinstance(self.modality, EvidenceModality):
            raise EvidenceValidationError(
                "modality must be an EvidenceModality"
            )
        if not isinstance(self.status, EvidenceStatus):
            raise EvidenceValidationError(
                "status must be an EvidenceStatus"
            )
        if not isinstance(self.classification, ClassificationLevel):
            raise EvidenceValidationError(
                "classification must be a ClassificationLevel"
            )

        object.__setattr__(
            self,
            "tags",
            normalize_string_tuple(
                self.tags,
                field_name="tags",
                sort_values=True,
            ),
        )

        if len(set(self.parent_evidence_ids)) != len(self.parent_evidence_ids):
            raise EvidenceValidationError(
                "parent_evidence_ids must not contain duplicates"
            )

        if self.evidence_id in self.parent_evidence_ids:
            raise EvidenceValidationError(
                "Evidence cannot be its own parent"
            )

    @classmethod
    def create(
        cls,
        *,
        content: EvidenceContent,
        origin: EvidenceOrigin,
        provenance: EvidenceProvenance,
        temporal_scope: EvidenceTemporalScope,
        uncertainty: EvidenceUncertainty,
        modality: EvidenceModality,
        status: EvidenceStatus = EvidenceStatus.ACTIVE,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        tags: Iterable[str] = (),
        parent_evidence_ids: Iterable[EvidenceId] = (),
    ) -> "EvidenceRecord":
        normalized_tags = tuple(sorted(tags))
        normalized_parents = tuple(sorted(parent_evidence_ids))

        identity_payload = {
            "content_id": content.content_id,
            "origin": origin,
            "provenance": provenance,
            "temporal_scope": temporal_scope,
            "uncertainty": uncertainty,
            "modality": modality,
            "classification": classification,
            "tags": normalized_tags,
            "parent_evidence_ids": normalized_parents,
        }

        return cls(
            evidence_id=EvidenceId.from_payload(identity_payload),
            content=content,
            origin=origin,
            provenance=provenance,
            temporal_scope=temporal_scope,
            uncertainty=uncertainty,
            modality=modality,
            status=status,
            classification=classification,
            tags=normalized_tags,
            parent_evidence_ids=normalized_parents,
        )


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    """Context-specific evaluation that does not mutate Evidence."""

    assessment_id: EvidenceAssessmentId
    evidence_id: EvidenceId
    reasoning_context_id: str
    assessor_id: str
    method: AssessmentMethod
    sequence: int
    rationale: str
    source_reliability: Decimal | None = None
    content_credibility: Decimal | None = None
    relevance: Decimal | None = None
    freshness: Decimal | None = None
    independence: Decimal | None = None
    diagnosticity: Decimal | None = None
    completeness: Decimal | None = None
    consistency: Decimal | None = None
    decision_impact: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.assessment_id, EvidenceAssessmentId):
            raise EvidenceValidationError(
                "assessment_id must be an EvidenceAssessmentId"
            )
        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )
        if not isinstance(self.method, AssessmentMethod):
            raise EvidenceValidationError(
                "method must be an AssessmentMethod"
            )

        object.__setattr__(
            self,
            "reasoning_context_id",
            normalize_text(
                self.reasoning_context_id,
                field_name="reasoning_context_id",
            ),
        )
        object.__setattr__(
            self,
            "assessor_id",
            normalize_text(self.assessor_id, field_name="assessor_id"),
        )
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(self.sequence, field_name="sequence"),
        )
        object.__setattr__(
            self,
            "rationale",
            normalize_text(self.rationale, field_name="rationale"),
        )

        score_fields = (
            "source_reliability",
            "content_credibility",
            "relevance",
            "freshness",
            "independence",
            "diagnosticity",
            "completeness",
            "consistency",
            "decision_impact",
        )

        for field_name in score_fields:
            object.__setattr__(
                self,
                field_name,
                validate_unit_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceId,
        reasoning_context_id: str,
        assessor_id: str,
        method: AssessmentMethod,
        sequence: int,
        rationale: str,
        source_reliability: Decimal | int | str | None = None,
        content_credibility: Decimal | int | str | None = None,
        relevance: Decimal | int | str | None = None,
        freshness: Decimal | int | str | None = None,
        independence: Decimal | int | str | None = None,
        diagnosticity: Decimal | int | str | None = None,
        completeness: Decimal | int | str | None = None,
        consistency: Decimal | int | str | None = None,
        decision_impact: Decimal | int | str | None = None,
    ) -> "EvidenceAssessment":
        payload = {
            "evidence_id": evidence_id,
            "reasoning_context_id": reasoning_context_id,
            "assessor_id": assessor_id,
            "method": method,
            "sequence": sequence,
            "rationale": rationale,
            "source_reliability": source_reliability,
            "content_credibility": content_credibility,
            "relevance": relevance,
            "freshness": freshness,
            "independence": independence,
            "diagnosticity": diagnosticity,
            "completeness": completeness,
            "consistency": consistency,
            "decision_impact": decision_impact,
        }

        return cls(
            assessment_id=EvidenceAssessmentId.from_payload(payload),
            evidence_id=evidence_id,
            reasoning_context_id=reasoning_context_id,
            assessor_id=assessor_id,
            method=method,
            sequence=sequence,
            rationale=rationale,
            source_reliability=source_reliability,
            content_credibility=content_credibility,
            relevance=relevance,
            freshness=freshness,
            independence=independence,
            diagnosticity=diagnosticity,
            completeness=completeness,
            consistency=consistency,
            decision_impact=decision_impact,
        )


@dataclass(frozen=True, slots=True)
class EvidenceStatusEvent:
    """Append-only event describing a change in Evidence standing."""

    event_id: EvidenceStatusEventId
    evidence_id: EvidenceId
    previous_status: EvidenceStatus
    new_status: EvidenceStatus
    sequence: int
    reason: str
    related_evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EvidenceStatusEventId):
            raise EvidenceValidationError(
                "event_id must be an EvidenceStatusEventId"
            )
        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )
        if not isinstance(self.previous_status, EvidenceStatus):
            raise EvidenceValidationError(
                "previous_status must be an EvidenceStatus"
            )
        if not isinstance(self.new_status, EvidenceStatus):
            raise EvidenceValidationError(
                "new_status must be an EvidenceStatus"
            )
        if self.previous_status is self.new_status:
            raise EvidenceValidationError(
                "status event must change Evidence standing"
            )

        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(self.sequence, field_name="sequence"),
        )
        object.__setattr__(
            self,
            "reason",
            normalize_text(self.reason, field_name="reason"),
        )

        if len(set(self.related_evidence_ids)) != len(
            self.related_evidence_ids
        ):
            raise EvidenceValidationError(
                "related_evidence_ids must not contain duplicates"
            )

    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceId,
        previous_status: EvidenceStatus,
        new_status: EvidenceStatus,
        sequence: int,
        reason: str,
        related_evidence_ids: Iterable[EvidenceId] = (),
    ) -> "EvidenceStatusEvent":
        normalized_related = tuple(sorted(related_evidence_ids))

        payload = {
            "evidence_id": evidence_id,
            "previous_status": previous_status,
            "new_status": new_status,
            "sequence": sequence,
            "reason": reason,
            "related_evidence_ids": normalized_related,
        }

        return cls(
            event_id=EvidenceStatusEventId.from_payload(payload),
            evidence_id=evidence_id,
            previous_status=previous_status,
            new_status=new_status,
            sequence=sequence,
            reason=reason,
            related_evidence_ids=normalized_related,
        )
EOF

cat > "$EVIDENCE_DIR/__init__.py" <<'EOF'
"""Stable public surface for Genesis II-A4 Canonical Evidence contracts."""

from .contracts import (
    BeliefMass,
    EvidenceAssessment,
    EvidenceContent,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceStatusEvent,
    EvidenceTemporalScope,
    EvidenceUncertainty,
)
from .enums import (
    AssessmentMethod,
    ClassificationLevel,
    EvidenceModality,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatus,
    UncertaintyKind,
)
from .errors import (
    EvidenceError,
    EvidenceIdentityError,
    EvidenceRelationshipError,
    EvidenceSerializationError,
    EvidenceTemporalError,
    EvidenceUncertaintyError,
    EvidenceValidationError,
)
from .identifiers import (
    CanonicalEvidenceIdentifier,
    EvidenceAssessmentId,
    EvidenceContentId,
    EvidenceId,
    EvidenceRelationshipId,
    EvidenceStatusEventId,
)
from .serialization import (
    canonical_bytes,
    canonical_json,
    canonical_sha256,
    to_canonical_primitive,
)

__all__ = [
    "AssessmentMethod",
    "BeliefMass",
    "CanonicalEvidenceIdentifier",
    "ClassificationLevel",
    "EvidenceAssessment",
    "EvidenceAssessmentId",
    "EvidenceContent",
    "EvidenceContentId",
    "EvidenceError",
    "EvidenceId",
    "EvidenceIdentityError",
    "EvidenceModality",
    "EvidenceOrigin",
    "EvidenceProvenance",
    "EvidenceProvenanceStep",
    "EvidenceRecord",
    "EvidenceRelationship",
    "EvidenceRelationshipError",
    "EvidenceRelationshipId",
    "EvidenceRelationshipType",
    "EvidenceSerializationError",
    "EvidenceSourceType",
    "EvidenceStatus",
    "EvidenceStatusEvent",
    "EvidenceStatusEventId",
    "EvidenceTemporalError",
    "EvidenceTemporalScope",
    "EvidenceUncertainty",
    "EvidenceUncertaintyError",
    "EvidenceValidationError",
    "UncertaintyKind",
    "canonical_bytes",
    "canonical_json",
    "canonical_sha256",
    "to_canonical_primitive",
]
EOF

cat > "$TEST_FILE" <<'EOF'
"""Genesis II-A4 constitutional tests for canonical Evidence contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from core.reasoning.evidence import (
    AssessmentMethod,
    BeliefMass,
    ClassificationLevel,
    EvidenceAssessment,
    EvidenceContent,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatus,
    EvidenceStatusEvent,
    EvidenceTemporalError,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    EvidenceUncertaintyError,
    EvidenceValidationError,
    UncertaintyKind,
    canonical_json,
)


FIXED_TIME = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)


def build_record(
    *,
    statement: str = "The observed system completed verification.",
    source_id: str = "verification-suite",
    observed_at: datetime = FIXED_TIME,
) -> EvidenceRecord:
    content = EvidenceContent(
        statement=statement,
        media_type="text/plain",
        language="en",
        attributes=(
            ("phase", "genesis-ii-a4"),
            ("domain", "reasoning"),
        ),
    )

    origin = EvidenceOrigin(
        source_type=EvidenceSourceType.TOOL,
        source_id=source_id,
        immediate_source_id="dev/verify_genesis_2a4.sh",
        origin_id="jarvis-repository",
        source_family_id="genesis-verification",
        collection_event_id="genesis-ii-a4-contract-test",
        dependency_group_ids=("local-runtime",),
    )

    provenance = EvidenceProvenance(
        steps=(
            EvidenceProvenanceStep(
                sequence=0,
                actor="pytest",
                mechanism="deterministic-fixture",
                input_ids=("genesis-ii-a4",),
                transformation="construct immutable Evidence fixture",
            ),
        )
    )

    temporal_scope = EvidenceTemporalScope(
        recorded_at=FIXED_TIME,
        observed_at=observed_at,
        valid_from=observed_at,
    )

    uncertainty = EvidenceUncertainty(
        kind=UncertaintyKind.PROBABILITY,
        probability=Decimal("0.95"),
    )

    return EvidenceRecord.create(
        content=content,
        origin=origin,
        provenance=provenance,
        temporal_scope=temporal_scope,
        uncertainty=uncertainty,
        modality=EvidenceModality.OBSERVATIONAL,
        status=EvidenceStatus.ACTIVE,
        classification=ClassificationLevel.INTERNAL,
        tags=("verification", "genesis"),
    )


def test_evidence_record_is_deterministic() -> None:
    first = build_record()
    second = build_record()

    assert first == second
    assert first.evidence_id == second.evidence_id
    assert canonical_json(first) == canonical_json(second)


def test_content_identity_is_distinct_from_record_identity() -> None:
    first = build_record(source_id="source-a")
    second = build_record(source_id="source-b")

    assert first.content.content_id == second.content.content_id
    assert first.evidence_id != second.evidence_id


def test_identical_content_does_not_imply_independent_corroboration() -> None:
    first = build_record(source_id="mirror-a")
    second = build_record(source_id="mirror-b")

    assert first.content.content_id == second.content.content_id

    relationship = EvidenceRelationship.create(
        source_evidence_id=first.evidence_id,
        target_evidence_id=second.evidence_id,
        relationship_type=EvidenceRelationshipType.SAME_ORIGIN_AS,
        rationale="Both records descend from one underlying report.",
    )

    assert relationship.source_evidence_id == first.evidence_id
    assert relationship.target_evidence_id == second.evidence_id
    assert (
        relationship.relationship_type
        is EvidenceRelationshipType.SAME_ORIGIN_AS
    )


def test_evidence_contracts_are_immutable() -> None:
    record = build_record()

    with pytest.raises(FrozenInstanceError):
        record.status = EvidenceStatus.SUPERSEDED  # type: ignore[misc]


def test_evidence_revision_uses_status_event() -> None:
    record = build_record()
    replacement = build_record(
        statement="The corrected system result completed verification."
    )

    event = EvidenceStatusEvent.create(
        evidence_id=record.evidence_id,
        previous_status=EvidenceStatus.ACTIVE,
        new_status=EvidenceStatus.SUPERSEDED,
        sequence=1,
        reason="A corrected Evidence record was admitted.",
        related_evidence_ids=(replacement.evidence_id,),
    )

    assert event.previous_status is EvidenceStatus.ACTIVE
    assert event.new_status is EvidenceStatus.SUPERSEDED
    assert event.related_evidence_ids == (replacement.evidence_id,)
    assert record.status is EvidenceStatus.ACTIVE


def test_assessment_is_context_specific() -> None:
    record = build_record()

    mission_assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:mission-alpha",
        assessor_id="reasoning-director",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale="Directly relevant to mission-alpha verification.",
        source_reliability="0.90",
        content_credibility="0.95",
        relevance="1.0",
        freshness="1.0",
        independence="0.80",
        diagnosticity="0.90",
    )

    unrelated_assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:mission-beta",
        assessor_id="reasoning-director",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale="The Evidence is not relevant to mission-beta.",
        source_reliability="0.90",
        content_credibility="0.95",
        relevance="0.05",
        freshness="1.0",
        independence="0.80",
        diagnosticity="0.05",
    )

    assert mission_assessment.evidence_id == unrelated_assessment.evidence_id
    assert mission_assessment.assessment_id != unrelated_assessment.assessment_id
    assert mission_assessment.relevance == Decimal("1")
    assert unrelated_assessment.relevance == Decimal("0.05")


def test_source_reliability_and_content_credibility_are_separate() -> None:
    record = build_record()

    assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:credibility-test",
        assessor_id="constitutional-test",
        method=AssessmentMethod.HUMAN_REVIEW,
        sequence=0,
        rationale="Reliable source, but content remains partly unverified.",
        source_reliability="0.95",
        content_credibility="0.60",
    )

    assert assessment.source_reliability == Decimal("0.95")
    assert assessment.content_credibility == Decimal("0.6")
    assert assessment.source_reliability != assessment.content_credibility


def test_uncertainty_is_typed() -> None:
    probability = EvidenceUncertainty(
        kind=UncertaintyKind.PROBABILITY,
        probability=Decimal("0.70"),
    )

    interval = EvidenceUncertainty(
        kind=UncertaintyKind.INTERVAL,
        lower_bound=Decimal("0.50"),
        upper_bound=Decimal("0.80"),
    )

    qualitative = EvidenceUncertainty(
        kind=UncertaintyKind.QUALITATIVE,
        qualitative_label="moderate",
    )

    likelihood = EvidenceUncertainty(
        kind=UncertaintyKind.LIKELIHOOD,
        likelihood=Decimal("3.5"),
    )

    belief_function = EvidenceUncertainty(
        kind=UncertaintyKind.BELIEF_FUNCTION,
        belief_masses=(
            BeliefMass(
                focal_set=("hypothesis-a",),
                mass=Decimal("0.6"),
            ),
            BeliefMass(
                focal_set=("hypothesis-a", "hypothesis-b"),
                mass=Decimal("0.4"),
            ),
        ),
    )

    assert probability.kind is UncertaintyKind.PROBABILITY
    assert interval.kind is UncertaintyKind.INTERVAL
    assert qualitative.kind is UncertaintyKind.QUALITATIVE
    assert likelihood.kind is UncertaintyKind.LIKELIHOOD
    assert belief_function.kind is UncertaintyKind.BELIEF_FUNCTION


def test_incompatible_uncertainty_values_are_rejected() -> None:
    with pytest.raises(EvidenceUncertaintyError):
        EvidenceUncertainty(
            kind=UncertaintyKind.PROBABILITY,
            probability=Decimal("0.75"),
            qualitative_label="high",
        )


def test_belief_function_mass_must_sum_to_one() -> None:
    with pytest.raises(EvidenceUncertaintyError):
        EvidenceUncertainty(
            kind=UncertaintyKind.BELIEF_FUNCTION,
            belief_masses=(
                BeliefMass(
                    focal_set=("hypothesis-a",),
                    mass=Decimal("0.4"),
                ),
                BeliefMass(
                    focal_set=("hypothesis-b",),
                    mass=Decimal("0.4"),
                ),
            ),
        )


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(EvidenceTemporalError):
        EvidenceTemporalScope(
            recorded_at=datetime(2026, 7, 20, 12, 0),
        )


def test_invalid_validity_interval_is_rejected() -> None:
    with pytest.raises(EvidenceTemporalError):
        EvidenceTemporalScope(
            recorded_at=FIXED_TIME,
            valid_from=FIXED_TIME,
            valid_until=FIXED_TIME - timedelta(seconds=1),
        )


def test_float_scores_are_rejected() -> None:
    record = build_record()

    with pytest.raises(EvidenceValidationError):
        EvidenceAssessment.create(
            evidence_id=record.evidence_id,
            reasoning_context_id="context:float-test",
            assessor_id="constitutional-test",
            method=AssessmentMethod.RULE_BASED,
            sequence=0,
            rationale="Floating point is not canonical.",
            relevance=0.5,
        )


def test_modality_is_explicit() -> None:
    observational = build_record()

    predictive = EvidenceRecord.create(
        content=observational.content,
        origin=observational.origin,
        provenance=observational.provenance,
        temporal_scope=observational.temporal_scope,
        uncertainty=observational.uncertainty,
        modality=EvidenceModality.PREDICTIVE,
        classification=observational.classification,
        tags=observational.tags,
    )

    assert observational.modality is EvidenceModality.OBSERVATIONAL
    assert predictive.modality is EvidenceModality.PREDICTIVE
    assert observational.evidence_id != predictive.evidence_id


def test_tag_order_does_not_change_identity() -> None:
    base = build_record()

    first = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        tags=("alpha", "beta"),
    )

    second = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        tags=("beta", "alpha"),
    )

    assert first.tags == ("alpha", "beta")
    assert first.evidence_id == second.evidence_id


def test_provenance_sequence_must_be_contiguous() -> None:
    with pytest.raises(EvidenceValidationError):
        EvidenceProvenance(
            steps=(
                EvidenceProvenanceStep(
                    sequence=1,
                    actor="test",
                    mechanism="invalid-sequence",
                ),
            )
        )


def test_public_contracts_do_not_execute_external_behavior() -> None:
    import core.reasoning.evidence.contracts as contracts
    import core.reasoning.evidence.identifiers as identifiers
    import core.reasoning.evidence.serialization as serialization

    prohibited_names = {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "sqlite3",
        "sqlalchemy",
        "random",
        "uuid4",
    }

    loaded_names = (
        set(vars(contracts))
        | set(vars(identifiers))
        | set(vars(serialization))
    )

    assert prohibited_names.isdisjoint(loaded_names)
EOF

cat > "$VERIFY_FILE" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

PASS_COUNT=0
FAIL_COUNT=0

print_header() {
    printf '\n'
    printf '%s\n' \
        "======================================================================"
    printf '%s\n' \
        "JARVIS GENESIS II-A4 — IMMUTABLE EVIDENCE CONTRACTS"
    printf '%s\n' \
        "======================================================================"
}

pass_check() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail_check() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
}

run_check() {
    local label="$1"
    shift

    if "$@" >/dev/null 2>&1; then
        pass_check "$label"
    else
        fail_check "$label"
    fi
}

print_header

run_check \
    "Canonical Evidence package structure" \
    test -f core/reasoning/evidence/__init__.py

run_check \
    "Evidence domain exceptions" \
    test -f core/reasoning/evidence/errors.py

run_check \
    "Canonical Evidence vocabularies" \
    test -f core/reasoning/evidence/enums.py

run_check \
    "Deterministic Evidence identifiers" \
    test -f core/reasoning/evidence/identifiers.py

run_check \
    "Immutable Evidence contracts" \
    test -f core/reasoning/evidence/contracts.py

run_check \
    "Deterministic canonical serialization" \
    test -f core/reasoning/evidence/serialization.py

run_check \
    "Evidence structural validation" \
    test -f core/reasoning/evidence/validation.py

run_check \
    "Genesis II-A4 architecture document" \
    test -f \
        docs/architecture/genesis/reasoning/GENESIS_II_A4_CANONICAL_EVIDENCE_MODEL.md

run_check \
    "ADR-0019 canonical Evidence decision" \
    test -f docs/decisions/ADR-0019-canonical-evidence-model.md

if "$PYTHON_BIN" -m compileall -q core/reasoning/evidence; then
    pass_check "Evidence package compilation"
else
    fail_check "Evidence package compilation"
fi

if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
from core.reasoning.evidence import (
    AssessmentMethod,
    EvidenceAssessment,
    EvidenceContent,
    EvidenceId,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatusEvent,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    UncertaintyKind,
    canonical_json,
)
PY
then
    pass_check "Stable public Evidence imports"
else
    fail_check "Stable public Evidence imports"
fi

if "$PYTHON_BIN" -m pytest -q \
    tests/test_genesis_2a4_evidence_contracts.py; then
    pass_check "Genesis II-A4 constitutional unit tests"
else
    fail_check "Genesis II-A4 constitutional unit tests"
fi

if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
from datetime import datetime, timezone
from decimal import Decimal

from core.reasoning.evidence import (
    EvidenceContent,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    UncertaintyKind,
    canonical_json,
)

fixed_time = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

def build():
    return EvidenceRecord.create(
        content=EvidenceContent(
            statement="Deterministic Evidence identity smoke test.",
        ),
        origin=EvidenceOrigin(
            source_type=EvidenceSourceType.TOOL,
            source_id="genesis-ii-a4-verifier",
        ),
        provenance=EvidenceProvenance(
            steps=(
                EvidenceProvenanceStep(
                    sequence=0,
                    actor="verify_genesis_2a4",
                    mechanism="smoke-test",
                ),
            )
        ),
        temporal_scope=EvidenceTemporalScope(
            recorded_at=fixed_time,
        ),
        uncertainty=EvidenceUncertainty(
            kind=UncertaintyKind.PROBABILITY,
            probability=Decimal("1"),
        ),
        modality=EvidenceModality.OBSERVATIONAL,
    )

first = build()
second = build()

assert first.evidence_id == second.evidence_id
assert canonical_json(first) == canonical_json(second)
PY
then
    pass_check "Deterministic Evidence identity smoke test"
else
    fail_check "Deterministic Evidence identity smoke test"
fi

if ! grep -R -nE \
    '(^|[[:space:]])(requests|urllib|socket|subprocess|sqlite3|sqlalchemy)([[:space:].]|$)' \
    core/reasoning/evidence \
    --include='*.py' \
    >/dev/null 2>&1
then
    pass_check "No network, persistence, or process dependencies"
else
    fail_check "No network, persistence, or process dependencies"
fi

if grep -Fq \
    "Evidence is not belief." \
    docs/architecture/genesis/reasoning/GENESIS_II_A4_CANONICAL_EVIDENCE_MODEL.md
then
    pass_check "Evidence and Belief constitutional separation"
else
    fail_check "Evidence and Belief constitutional separation"
fi

printf '%s\n' \
    "----------------------------------------------------------------------"
printf 'Checks passed : %s\n' "$PASS_COUNT"
printf 'Checks failed : %s\n' "$FAIL_COUNT"

if (( FAIL_COUNT == 0 )); then
    printf 'Overall status: EXCELLENT\n'
    printf '%s\n' \
        "======================================================================"
    exit 0
fi

printf 'Overall status: FAILED\n'
printf '%s\n' \
    "======================================================================"
exit 1
EOF

chmod +x "$VERIFY_FILE"

printf '\n'
printf '%s\n' \
    "======================================================================"
printf '%s\n' \
    "GENESIS II-A4 PHASE 2 INSTALLATION COMPLETE"
printf '%s\n' \
    "======================================================================"
printf 'Evidence package : %s\n' "$EVIDENCE_DIR"
printf 'Tests            : %s\n' "$TEST_FILE"
printf 'Verifier         : %s\n' "$VERIFY_FILE"
printf '\n'
printf '%s\n' \
    "Next command:"
printf '%s\n' \
    "PYTHON_BIN=<venv-python> ./dev/verify_genesis_2a4.sh"
