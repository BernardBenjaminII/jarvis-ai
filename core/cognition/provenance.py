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
