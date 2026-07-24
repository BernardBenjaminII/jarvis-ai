"""Canonical contracts for JARVIS Cognitive Representation.

Phase X-C2 extends the Representation subsystem while preserving the
stable Phase X-C1 segmentation API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------


def _empty_metadata() -> Mapping[str, str]:
    """Return a shared immutable empty metadata mapping."""
    return MappingProxyType({})


def _freeze_metadata(metadata: Mapping[str, str]) -> Mapping[str, str]:
    """Create an immutable defensive copy of metadata."""
    return MappingProxyType(dict(metadata))


# ----------------------------------------------------------------------
# Phase X-C1 artifact and segmentation contracts
# ----------------------------------------------------------------------


class ArtifactKind(str, Enum):
    """Supported source-artifact categories."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    DOCUMENT = "document"
    SOURCE_CODE = "source_code"
    UNKNOWN = "unknown"


class SegmentKind(str, Enum):
    """Canonical structural and semantic segment categories."""

    # Phase X-C1 stable values.
    SENTENCE = "sentence"
    HEADING = "heading"
    BULLET = "bullet"
    TABLE_ROW = "table_row"
    KEY_VALUE = "key_value"
    CODE = "code"

    # Phase X-C2 expanded categories.
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    QUOTE = "quote"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Half-open character interval within a source artifact."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("SourceSpan.start cannot be negative.")

        if self.end < self.start:
            raise ValueError(
                "SourceSpan.end cannot be less than SourceSpan.start."
            )

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Stable reference to an artifact entering Representation."""

    artifact_id: str
    kind: ArtifactKind = ArtifactKind.TEXT

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id cannot be empty.")


@dataclass(frozen=True, slots=True)
class SegmentationRequest:
    """Request for deterministic semantic segmentation."""

    artifact: ArtifactReference
    text: str
    metadata: Mapping[str, str] = field(default_factory=_empty_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def source_id(self) -> str:
        return self.artifact.artifact_id

    @property
    def segment_count(self) -> int:
        return len(self.segments)


@dataclass(frozen=True, slots=True)
class SemanticSegment:
    """A deterministic segment derived directly from a source artifact."""

    segment_id: str
    artifact: ArtifactReference
    ordinal: int
    kind: SegmentKind
    text: str
    span: SourceSpan
    metadata: Mapping[str, str] = field(default_factory=_empty_metadata)

    def __post_init__(self) -> None:
        if not self.segment_id.strip():
            raise ValueError("segment_id cannot be empty.")

        if self.ordinal < 0:
            raise ValueError("ordinal cannot be negative.")

        if not self.text:
            raise ValueError("SemanticSegment.text cannot be empty.")

        if self.span.length <= 0:
            raise ValueError("SemanticSegment.span must contain source text.")

        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def identifier(self) -> str:
        """X-C2-compatible cognitive-object identifier."""
        return self.segment_id

    @property
    def source_id(self) -> str:
        """Identifier of the source artifact."""
        return self.artifact.artifact_id


@dataclass(frozen=True, slots=True)
class SegmentationResult:
    """Complete deterministic segmentation result for one artifact."""

    artifact: ArtifactReference
    segments: Sequence[SemanticSegment]
    source_length: int
    segmentation_version: str

    def __post_init__(self) -> None:
        if self.source_length < 0:
            raise ValueError("source_length cannot be negative.")

        object.__setattr__(self, "segments", tuple(self.segments))

    @property
    def source_id(self) -> str:
        return self.artifact.artifact_id


    @property
    def segment_count(self) -> int:
        """Backward-compatible X-C1 API."""
        return len(self.segments)

# ----------------------------------------------------------------------
# Phase X-C2 cognitive representation contracts
# ----------------------------------------------------------------------


class PropositionTruth(str, Enum):
    """Current epistemic status assigned to a proposition."""

    UNKNOWN = "unknown"
    ASSERTED = "asserted"
    INFERRED = "inferred"
    CONTRADICTED = "contradicted"


class ClaimStrength(str, Enum):
    """Relative evidentiary strength of a claim."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True, slots=True)
class CognitiveObject:
    """Root contract for derived cognitive representations."""

    identifier: str
    source_id: str
    metadata: Mapping[str, str] = field(
        default_factory=_empty_metadata,
        kw_only=True,
    )

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("identifier cannot be empty.")

        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty.")

        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Sentence(CognitiveObject):
    """Sentence representation derived from a semantic segment."""

    text: str
    segment_id: str
    ordinal: int

    def __post_init__(self) -> None:
        CognitiveObject.__post_init__(self)

        if not self.text:
            raise ValueError("Sentence.text cannot be empty.")

        if not self.segment_id.strip():
            raise ValueError("segment_id cannot be empty.")

        if self.ordinal < 0:
            raise ValueError("ordinal cannot be negative.")


@dataclass(frozen=True, slots=True)
class Proposition(CognitiveObject):
    """Normalized subject-predicate-object proposition."""

    subject: str
    predicate: str
    object: str
    truth: PropositionTruth = PropositionTruth.UNKNOWN

    def __post_init__(self) -> None:
        CognitiveObject.__post_init__(self)

        if not self.subject.strip():
            raise ValueError("Proposition.subject cannot be empty.")

        if not self.predicate.strip():
            raise ValueError("Proposition.predicate cannot be empty.")

        if not self.object.strip():
            raise ValueError("Proposition.object cannot be empty.")


@dataclass(frozen=True, slots=True)
class Observation(CognitiveObject):
    """Source-grounded observation with bounded confidence."""

    statement: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        CognitiveObject.__post_init__(self)

        if not self.statement.strip():
            raise ValueError("Observation.statement cannot be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")


@dataclass(frozen=True, slots=True)
class Claim(CognitiveObject):
    """A proposition advanced as a claim."""

    statement: str
    strength: ClaimStrength = ClaimStrength.MODERATE

    def __post_init__(self) -> None:
        CognitiveObject.__post_init__(self)

        if not self.statement.strip():
            raise ValueError("Claim.statement cannot be empty.")


@dataclass(frozen=True, slots=True)
class Relationship(CognitiveObject):
    """Directed relationship between two represented objects."""

    source: str
    relation: str
    target: str

    def __post_init__(self) -> None:
        CognitiveObject.__post_init__(self)

        if not self.source.strip():
            raise ValueError("Relationship.source cannot be empty.")

        if not self.relation.strip():
            raise ValueError("Relationship.relation cannot be empty.")

        if not self.target.strip():
            raise ValueError("Relationship.target cannot be empty.")


@dataclass(frozen=True, slots=True)
class RepresentationBundle:
    """Representations derived from a single source artifact."""

    source_id: str
    segments: Sequence[SemanticSegment] = ()
    sentences: Sequence[Sentence] = ()
    propositions: Sequence[Proposition] = ()
    observations: Sequence[Observation] = ()
    claims: Sequence[Claim] = ()
    relationships: Sequence[Relationship] = ()

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty.")

        object.__setattr__(self, "segments", tuple(self.segments))
        object.__setattr__(self, "sentences", tuple(self.sentences))
        object.__setattr__(self, "propositions", tuple(self.propositions))
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "relationships", tuple(self.relationships))
