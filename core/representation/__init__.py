"""Stable public interface for JARVIS Cognitive Representation."""

from .contracts import (
    ArtifactKind,
    ArtifactReference,
    Claim,
    ClaimStrength,
    CognitiveObject,
    Observation,
    Proposition,
    PropositionTruth,
    Relationship,
    RepresentationBundle,
    SegmentKind,
    SegmentationRequest,
    SegmentationResult,
    SemanticSegment,
    Sentence,
    SourceSpan,
)
from .segmentation import (
    SEGMENTATION_VERSION,
    DeterministicSemanticSegmenter,
    segment_text,
)

__all__ = [
    # Phase X-C1 compatibility
    "ArtifactKind",
    "ArtifactReference",
    "SegmentationRequest",
    "SegmentationResult",
    "SemanticSegment",
    "SourceSpan",

    # Phase X-C2
    "Claim",
    "ClaimStrength",
    "CognitiveObject",
    "Observation",
    "Proposition",
    "PropositionTruth",
    "Relationship",
    "RepresentationBundle",
    "Sentence",

    # Shared
    "DeterministicSemanticSegmenter",
    "SEGMENTATION_VERSION",
    "SegmentKind",
    "segment_text",
]
