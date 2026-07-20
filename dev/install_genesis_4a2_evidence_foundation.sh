#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

COGNITION_ROOT="${PROJECT_ROOT}/core/cognition"
ARCHITECTURE_ROOT="${PROJECT_ROOT}/docs/architecture"
DECISIONS_ROOT="${PROJECT_ROOT}/docs/decisions"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-A2 — PART 1 EVIDENCE FOUNDATION"
echo "======================================================================"
echo
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo

if [[ ! -d "${PROJECT_ROOT}/core" ]]; then
    echo "[FAIL] Missing core directory: ${PROJECT_ROOT}/core"
    exit 1
fi

required_files=(
    "${COGNITION_ROOT}/contracts.py"
    "${COGNITION_ROOT}/enums.py"
    "${COGNITION_ROOT}/errors.py"
    "${COGNITION_ROOT}/identifiers.py"
    "${COGNITION_ROOT}/serialization.py"
    "${COGNITION_ROOT}/validation.py"
    "${COGNITION_ROOT}/observation.py"
)

for required_file in "${required_files[@]}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "[FAIL] Missing Genesis IV-A1 prerequisite:"
        echo "       ${required_file}"
        exit 1
    fi
done

if ! "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    echo "[FAIL] Python interpreter unavailable: ${PYTHON_BIN}"
    exit 1
fi

mkdir -p \
    "${COGNITION_ROOT}" \
    "${ARCHITECTURE_ROOT}" \
    "${DECISIONS_ROOT}"

cat > "${COGNITION_ROOT}/provenance.py" <<'PYEOF'
"""Immutable provenance contracts for Genesis IV-A2.

Provenance records where evidence came from and how it entered the cognition
layer. Provenance does not assert truth. It preserves traceability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .contracts import Metadata, SourceReference, normalize_metadata
from .errors import CognitionValidationError
from .normalization import normalize_display_text
from .serialization import canonical_fingerprint


GENESIS_IV_A2_SCHEMA_VERSION = "4.2.0"


class ProvenanceKind(str, Enum):
    """Constitutional provenance classifications."""

    DOCUMENT = "document"
    REPRESENTATION_SEGMENT = "representation_segment"
    STRUCTURED_RECORD = "structured_record"
    SENSOR_READING = "sensor_reading"
    OPERATOR_ENTRY = "operator_entry"
    SYSTEM_EVENT = "system_event"
    DERIVED_REFERENCE = "derived_reference"


class AcquisitionMethod(str, Enum):
    """How source material entered the system."""

    DIRECT = "direct"
    IMPORTED = "imported"
    EXTRACTED = "extracted"
    TRANSCRIBED = "transcribed"
    OBSERVED = "observed"
    GENERATED = "generated"
    UNKNOWN = "unknown"


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    return normalize_display_text(value)


def _normalize_string_tuple(
    values: Iterable[str],
) -> tuple[str, ...]:
    normalized = {
        normalize_display_text(value)
        for value in values
    }

    return tuple(sorted(normalized))


def make_provenance_id(payload: object) -> str:
    """Create a deterministic provenance identifier."""

    return f"cog_provenance_{canonical_fingerprint(payload)[:32]}"


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """Immutable record describing an evidence source."""

    source: SourceReference
    kind: ProvenanceKind
    acquisition_method: AcquisitionMethod = AcquisitionMethod.UNKNOWN
    origin_system: str | None = None
    origin_actor: str | None = None
    parent_provenance_ids: tuple[str, ...] = ()
    metadata: Metadata = ()
    schema_version: str = GENESIS_IV_A2_SCHEMA_VERSION
    provenance_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceReference):
            raise CognitionValidationError(
                "ProvenanceRecord.source must be a SourceReference."
            )

        if not isinstance(self.kind, ProvenanceKind):
            try:
                object.__setattr__(
                    self,
                    "kind",
                    ProvenanceKind(str(self.kind)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported provenance kind: {self.kind!r}"
                ) from exc

        if not isinstance(
            self.acquisition_method,
            AcquisitionMethod,
        ):
            try:
                object.__setattr__(
                    self,
                    "acquisition_method",
                    AcquisitionMethod(str(self.acquisition_method)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported acquisition method: "
                    f"{self.acquisition_method!r}"
                ) from exc

        object.__setattr__(
            self,
            "origin_system",
            _normalize_optional_text(self.origin_system),
        )
        object.__setattr__(
            self,
            "origin_actor",
            _normalize_optional_text(self.origin_actor),
        )
        object.__setattr__(
            self,
            "parent_provenance_ids",
            _normalize_string_tuple(self.parent_provenance_ids),
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

        identity_payload = self.identity_payload()
        expected_id = make_provenance_id(identity_payload)

        if self.provenance_id:
            supplied_id = normalize_display_text(self.provenance_id)

            if supplied_id != expected_id:
                raise CognitionValidationError(
                    "Provenance identifier does not match canonical content."
                )

            object.__setattr__(
                self,
                "provenance_id",
                supplied_id,
            )
        else:
            object.__setattr__(
                self,
                "provenance_id",
                expected_id,
            )

    def identity_payload(self) -> dict[str, object]:
        """Return content that constitutionally determines identity."""

        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "kind": self.kind.value,
            "acquisition_method": self.acquisition_method.value,
            "origin_system": self.origin_system,
            "origin_actor": self.origin_actor,
            "parent_provenance_ids": self.parent_provenance_ids,
            "metadata": self.metadata,
        }
PYEOF

cat > "${COGNITION_ROOT}/evidence.py" <<'PYEOF'
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
PYEOF

cat > "${COGNITION_ROOT}/evidence_chain.py" <<'PYEOF'
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
PYEOF

cat > "${COGNITION_ROOT}/evidence_validation.py" <<'PYEOF'
"""Validation for Genesis IV-A2 evidence objects."""

from __future__ import annotations

from .errors import CognitionValidationError
from .evidence import EvidenceRecord, make_evidence_id
from .evidence_chain import (
    EvidenceChain,
    EvidenceChainStatus,
    make_evidence_chain_id,
)
from .provenance import (
    ProvenanceRecord,
    make_provenance_id,
)


def validate_provenance_record(
    record: ProvenanceRecord,
) -> None:
    """Validate provenance structure and deterministic identity."""

    if not isinstance(record, ProvenanceRecord):
        raise CognitionValidationError(
            "Expected a ProvenanceRecord."
        )

    expected_id = make_provenance_id(record.identity_payload())

    if record.provenance_id != expected_id:
        raise CognitionValidationError(
            "Provenance identity verification failed."
        )

    if record.provenance_id in record.parent_provenance_ids:
        raise CognitionValidationError(
            "Provenance records may not directly parent themselves."
        )


def validate_evidence_record(
    record: EvidenceRecord,
) -> None:
    """Validate evidence structure and deterministic identity."""

    if not isinstance(record, EvidenceRecord):
        raise CognitionValidationError(
            "Expected an EvidenceRecord."
        )

    validate_provenance_record(record.provenance)

    expected_id = make_evidence_id(record.identity_payload())

    if record.evidence_id != expected_id:
        raise CognitionValidationError(
            "Evidence identity verification failed."
        )

    if len(record.observation_ids) != len(
        set(record.observation_ids)
    ):
        raise CognitionValidationError(
            "Evidence observation identifiers must be unique."
        )


def validate_evidence_chain(
    chain: EvidenceChain,
) -> None:
    """Validate an evidence chain and all contained evidence."""

    if not isinstance(chain, EvidenceChain):
        raise CognitionValidationError(
            "Expected an EvidenceChain."
        )

    for record in chain.evidence:
        validate_evidence_record(record)

    expected_id = make_evidence_chain_id(
        chain.identity_payload()
    )

    if chain.chain_id != expected_id:
        raise CognitionValidationError(
            "Evidence-chain identity verification failed."
        )

    evidence_ids = tuple(
        record.evidence_id
        for record in chain.evidence
    )

    if len(evidence_ids) != len(set(evidence_ids)):
        raise CognitionValidationError(
            "Evidence-chain records must be unique."
        )

    if (
        chain.status is EvidenceChainStatus.CONTESTED
        and not chain.is_contested
    ):
        raise CognitionValidationError(
            "A contested chain requires supporting and opposing evidence."
        )


def validate_evidence_object(value: object) -> None:
    """Dispatch validation for Genesis IV-A2 evidence objects."""

    if isinstance(value, ProvenanceRecord):
        validate_provenance_record(value)
        return

    if isinstance(value, EvidenceRecord):
        validate_evidence_record(value)
        return

    if isinstance(value, EvidenceChain):
        validate_evidence_chain(value)
        return

    raise CognitionValidationError(
        "Unsupported Genesis IV-A2 evidence object."
    )
PYEOF

cat > "${COGNITION_ROOT}/__init__.py" <<'PYEOF'
"""Genesis IV cognition-domain public API."""

from .confidence import (
    ConfidenceAssessment,
    ConfidenceFactors,
    ExtractionQuality,
    SourceReliability,
    assess_confidence,
    clamp_confidence,
    confidence_band,
    confidence_for_direct_source,
)
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
from .evidence import (
    EvidenceDirection,
    EvidenceKind,
    EvidenceQuality,
    EvidenceRecord,
    make_evidence_id,
)
from .evidence_chain import (
    EvidenceChain,
    EvidenceChainStatus,
    make_evidence_chain_id,
)
from .evidence_validation import (
    validate_evidence_chain,
    validate_evidence_object,
    validate_evidence_record,
    validate_provenance_record,
)
from .extraction import (
    ExtractionPattern,
    ExtractionResult,
    ExtractionSource,
    ObservationCandidate,
    extract_candidates,
    extract_many,
    structured_candidate,
)
from .identifiers import (
    make_cognition_id,
    normalize_kind,
    parse_cognition_id,
    validate_cognition_id,
    verify_cognition_id,
)
from .normalization import (
    NormalizedObservationValue,
    NormalizedQuantity,
    infer_value_kind,
    normalize_boolean_text,
    normalize_concept,
    normalize_decimal_text,
    normalize_display_text,
    normalize_identifier_token,
    normalize_integer_text,
    normalize_observation_value,
    normalize_unicode,
    normalize_unit,
    normalize_whitespace,
    parse_quantity,
)
from .observation import (
    ObservationBatch,
    ObservationConstruction,
    ObservationEngine,
    build_observation,
    observe_source,
)
from .provenance import (
    GENESIS_IV_A2_SCHEMA_VERSION,
    AcquisitionMethod,
    ProvenanceKind,
    ProvenanceRecord,
    make_provenance_id,
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
    "GENESIS_IV_A2_SCHEMA_VERSION",
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
    "ConfidenceAssessment",
    "ConfidenceFactors",
    "ExtractionQuality",
    "SourceReliability",
    "ExtractionPattern",
    "ExtractionResult",
    "ExtractionSource",
    "ObservationCandidate",
    "NormalizedObservationValue",
    "NormalizedQuantity",
    "ObservationBatch",
    "ObservationConstruction",
    "ObservationEngine",
    "AcquisitionMethod",
    "ProvenanceKind",
    "ProvenanceRecord",
    "EvidenceDirection",
    "EvidenceKind",
    "EvidenceQuality",
    "EvidenceRecord",
    "EvidenceChain",
    "EvidenceChainStatus",
    "assess_confidence",
    "build_observation",
    "canonical_fingerprint",
    "canonical_json",
    "canonicalize",
    "clamp_confidence",
    "confidence_band",
    "confidence_for_direct_source",
    "decimal_to_string",
    "extract_candidates",
    "extract_many",
    "infer_value_kind",
    "make_cognition_id",
    "make_evidence_chain_id",
    "make_evidence_id",
    "make_provenance_id",
    "normalize_boolean_text",
    "normalize_concept",
    "normalize_confidence",
    "normalize_decimal_text",
    "normalize_display_text",
    "normalize_identifier_token",
    "normalize_integer_text",
    "normalize_kind",
    "normalize_metadata",
    "normalize_observation_value",
    "normalize_unicode",
    "normalize_unit",
    "normalize_whitespace",
    "observe_source",
    "parse_cognition_id",
    "parse_quantity",
    "pretty_json",
    "structured_candidate",
    "validate_cognition_id",
    "validate_cognitive_object",
    "validate_evidence_chain",
    "validate_evidence_object",
    "validate_evidence_record",
    "validate_observation",
    "validate_observation_value",
    "validate_provenance_record",
    "validate_source_reference",
    "verify_cognition_id",
]
PYEOF

cat > "${ARCHITECTURE_ROOT}/genesis_iv_a2_evidence_association.md" <<'MDEOF'
# Genesis IV-A2 — Evidence Association Architecture

## Status

Implementation in progress.

Part 1 establishes the evidence constitution and immutable contracts.

## Purpose

Genesis IV-A2 introduces the permanent evidence layer between direct
observations and higher cognition.

The evidence layer answers:

- What supports an observation?
- What opposes it?
- Where did the evidence originate?
- How was it acquired?
- Can the evidence be reproduced and audited?
- Is the evidence chain contested or incomplete?

## Pipeline

```text
Represented Knowledge
        ↓
Observation
        ↓
Provenance Record
        ↓
Evidence Record
        ↓
Evidence Chain
        ↓
Claim Extraction
        ↓
Relationship Discovery
        ↓
Hypothesis Construction
        ↓
Interpretation
Constitutional Objects
ProvenanceRecord

A provenance record identifies:

the source reference;
provenance classification;
acquisition method;
source system or actor;
parent provenance records;
immutable metadata.

Provenance records do not declare truth.

EvidenceRecord

An evidence record associates:

one or more observations;
one provenance record;
an evidence classification;
a direction;
a quality rating;
confidence in the evidence record;
optional description and metadata.

Evidence direction is explicit:

supports;
opposes;
neutral.
EvidenceChain

An evidence chain groups evidence around a cognitive subject.

The subject may later be:

an observation;
a claim;
a relationship;
a hypothesis;
an interpretation.

Evidence chains preserve supporting and opposing material rather than erasing
disagreement.

Determinism

Every Genesis IV-A2 object has a deterministic identifier derived from its
canonical constitutional content.

Equivalent objects must produce identical identifiers regardless of input
ordering.

Separation of Concerns

The evidence layer does not:

infer claims;
decide which interpretation is correct;
generate plans;
execute actions;
suppress contradicting evidence.

Association policy belongs to the Part 2 association engine.

Phase Deliveries
Part 1 — Evidence Foundation
provenance contracts;
evidence contracts;
evidence-chain contracts;
deterministic identifiers;
validation;
public exports;
architectural documentation.
Part 2 — Association Engine
deterministic association rules;
candidate association;
evidence deduplication;
source and observation matching;
chain construction;
contested-chain detection.
Part 3 — Certification
unit tests;
verifier;
regression suite;
integration checks;
architecture fingerprint;
final phase documentation.
MDEOF

cat > "${DECISIONS_ROOT}/ADR-0018-genesis-iv-evidence-constitution.md" <<'MDEOF'

ADR-0018: Genesis IV Evidence Constitution

Status: Accepted
Decision scope: Genesis IV cognition architecture
Phase: Genesis IV-A2

Context

Reasoning directly over unstructured knowledge weakens traceability. A
conclusion may appear plausible without preserving an auditable path to the
material that supports or opposes it.

JARVIS requires a first-class evidence layer that remains separate from claims,
hypotheses, interpretations, plans, and executive actions.

Decision

JARVIS shall represent provenance, evidence, and evidence chains as immutable,
deterministically identified cognitive objects.

Evidence shall explicitly identify whether it supports, opposes, or remains
neutral toward its associated cognitive subject.

Contradicting evidence shall be retained.

Evidence confidence shall describe evidence quality and traceability rather
than the ultimate truth of a conclusion.

Constitutional Rules
Evidence must have provenance.
Provenance must resolve to a source reference.
Evidence must reference at least one observation.
Evidence direction must be explicit.
Supporting and opposing evidence may coexist.
Evidence chains must preserve disagreement.
Identifiers must be deterministic.
Input ordering must not alter canonical identity.
Evidence objects must be immutable.
Evidence association must not perform interpretation.
Missing evidence must not be silently fabricated.
Later cognition must be able to audit its complete evidence chain.
Consequences
Positive
conclusions become auditable;
contradictory sources remain visible;
evidence can be reused across claims;
reasoning can distinguish direct evidence from inference;
evidence chains can be inspected independently of final decisions.
Costs
additional cognitive objects must be stored;
association policies require careful deterministic rules;
evidence quality and conclusion confidence remain separate concepts;
unresolved conflicts must be represented rather than hidden.
Rejected Alternatives
Attach source identifiers directly to claims

Rejected because this collapses observation, evidence, and inference into one
object.

Allow evidence without provenance

Rejected because unsupported evidence cannot be audited.

Remove contradicting evidence during normalization

Rejected because normalization must not decide truth.

Use random UUIDs

Rejected because equivalent cognitive objects must converge to stable
identifiers.
MDEOF

echo "[PASS] Genesis IV-A2 Part 1 files installed"

echo
echo "Compiling cognition package..."
"${PYTHON_BIN}" -m compileall -q "${COGNITION_ROOT}"
echo "[PASS] Cognition package compilation"

echo
echo "Running public import verification..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
AcquisitionMethod,
EvidenceChain,
EvidenceChainStatus,
EvidenceDirection,
EvidenceKind,
EvidenceQuality,
EvidenceRecord,
ProvenanceKind,
ProvenanceRecord,
validate_evidence_chain,
validate_evidence_record,
validate_provenance_record,
)

assert AcquisitionMethod is not None
assert EvidenceChain is not None
assert EvidenceChainStatus is not None
assert EvidenceDirection is not None
assert EvidenceKind is not None
assert EvidenceQuality is not None
assert EvidenceRecord is not None
assert ProvenanceKind is not None
assert ProvenanceRecord is not None
assert validate_evidence_chain is not None
assert validate_evidence_record is not None
assert validate_provenance_record is not None

print("[PASS] Genesis IV-A2 public imports")
PYEOF

echo
echo "Running deterministic evidence smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from decimal import Decimal
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
AcquisitionMethod,
EvidenceChain,
EvidenceChainStatus,
EvidenceDirection,
EvidenceKind,
EvidenceQuality,
EvidenceRecord,
ExtractionSource,
ObservationEngine,
ProvenanceKind,
ProvenanceRecord,
SourceReliability,
canonical_json,
validate_evidence_chain,
)

source = ExtractionSource(
source_id="document:battery-report",
segment_id="segment-0001",
text="The battery voltage is 10.2 V.",
start_offset=0,
end_offset=30,
evidence_ids=("source-evidence-001",),
)

observation = ObservationEngine(
default_source_reliability=SourceReliability.HIGH,
).observe(source).observations[0]

provenance_a = ProvenanceRecord(
source=observation.source,
kind=ProvenanceKind.REPRESENTATION_SEGMENT,
acquisition_method=AcquisitionMethod.EXTRACTED,
origin_system="jarvis-representation",
metadata=(
("format", "text"),
("pipeline", "genesis-iv"),
),
)

provenance_b = ProvenanceRecord(
source=observation.source,
kind=ProvenanceKind.REPRESENTATION_SEGMENT,
acquisition_method=AcquisitionMethod.EXTRACTED,
origin_system="jarvis-representation",
metadata=(
("pipeline", "genesis-iv"),
("format", "text"),
),
)

assert provenance_a == provenance_b
assert provenance_a.provenance_id == provenance_b.provenance_id

evidence_a = EvidenceRecord.from_observation(
observation,
provenance=provenance_a,
kind=EvidenceKind.DIRECT,
direction=EvidenceDirection.SUPPORTS,
quality=EvidenceQuality.STRONG,
confidence=Decimal("0.95"),
description="Direct voltage reading from the source segment.",
)

evidence_b = EvidenceRecord.from_observation(
observation,
provenance=provenance_b,
kind=EvidenceKind.DIRECT,
direction=EvidenceDirection.SUPPORTS,
quality=EvidenceQuality.STRONG,
confidence=Decimal("0.95"),
description="Direct voltage reading from the source segment.",
)

assert evidence_a == evidence_b
assert evidence_a.evidence_id == evidence_b.evidence_id

chain_a = EvidenceChain(
subject_id=observation.observation_id,
evidence=(evidence_a,),
status=EvidenceChainStatus.COMPLETE,
confidence=Decimal("0.95"),
)

chain_b = EvidenceChain(
subject_id=observation.observation_id,
evidence=(evidence_b,),
status=EvidenceChainStatus.COMPLETE,
confidence=Decimal("0.95"),
)

assert chain_a == chain_b
assert chain_a.chain_id == chain_b.chain_id
assert canonical_json(chain_a) == canonical_json(chain_b)

validate_evidence_chain(chain_a)

print(f"[PASS] Provenance ID : {provenance_a.provenance_id}")
print(f"[PASS] Evidence ID : {evidence_a.evidence_id}")
print(f"[PASS] Chain ID : {chain_a.chain_id}")
print("[PASS] Deterministic evidence foundation")
PYEOF

echo
echo "Running contested-chain smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from decimal import Decimal
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
AcquisitionMethod,
EvidenceChain,
EvidenceChainStatus,
EvidenceDirection,
EvidenceKind,
EvidenceQuality,
EvidenceRecord,
ExtractionSource,
ObservationEngine,
ProvenanceKind,
ProvenanceRecord,
SourceReliability,
validate_evidence_chain,
)

source = ExtractionSource(
source_id="document:status-report",
text="The system status is operational.",
)

observation = ObservationEngine(
default_source_reliability=SourceReliability.HIGH,
).observe(source).observations[0]

provenance = ProvenanceRecord(
source=observation.source,
kind=ProvenanceKind.DOCUMENT,
acquisition_method=AcquisitionMethod.IMPORTED,
)

support = EvidenceRecord.from_observation(
observation,
provenance=provenance,
kind=EvidenceKind.DIRECT,
direction=EvidenceDirection.SUPPORTS,
quality=EvidenceQuality.STRONG,
confidence=Decimal("0.90"),
)

opposition = EvidenceRecord.from_observation(
observation,
provenance=provenance,
kind=EvidenceKind.CONTRADICTING,
direction=EvidenceDirection.OPPOSES,
quality=EvidenceQuality.MODERATE,
confidence=Decimal("0.65"),
description="A conflicting source interpretation exists.",
)

chain = EvidenceChain(
subject_id=observation.observation_id,
evidence=(support, opposition),
status=EvidenceChainStatus.CONTESTED,
confidence=Decimal("0.72"),
)

assert chain.is_contested
assert len(chain.supporting_evidence) == 1
assert len(chain.opposing_evidence) == 1

validate_evidence_chain(chain)

print("[PASS] Supporting and opposing evidence retained")
print("[PASS] Contested evidence chain validated")
PYEOF

echo
echo "Running immutability test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
AcquisitionMethod,
ProvenanceKind,
ProvenanceRecord,
SourceReference,
)

record = ProvenanceRecord(
source=SourceReference(
source_id="document:immutable",
),
kind=ProvenanceKind.DOCUMENT,
acquisition_method=AcquisitionMethod.DIRECT,
)

try:
    record.kind = ProvenanceKind.SYSTEM_EVENT
except FrozenInstanceError:
    print("[PASS] Evidence foundation contracts are immutable")
else:
    raise AssertionError(
        "ProvenanceRecord unexpectedly allowed mutation."
    )
PYEOF

echo
echo "======================================================================"
echo "GENESIS IV-A2 PART 1 INSTALLATION COMPLETE"
echo "======================================================================"
echo
echo "Installed:"
echo " core/cognition/provenance.py"
echo " core/cognition/evidence.py"
echo " core/cognition/evidence_chain.py"
echo " core/cognition/evidence_validation.py"
echo " core/cognition/init.py"
echo " docs/architecture/genesis_iv_a2_evidence_association.md"
echo " docs/decisions/ADR-0018-genesis-iv-evidence-constitution.md"
echo
echo "Verified:"
echo " Genesis IV-A1 prerequisites"
echo " Cognition package compilation"
echo " Stable public imports"
echo " Deterministic provenance identities"
echo " Deterministic evidence identities"
echo " Deterministic evidence-chain identities"
echo " Input-order independence"
echo " Contested evidence preservation"
echo " Immutable evidence contracts"
echo
echo "Overall status: EXCELLENT"
echo
