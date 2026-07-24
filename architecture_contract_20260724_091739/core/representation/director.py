"""Representation Director for JARVIS Cognitive Representation.

Phase X-C2 introduces the canonical orchestration entry point for
transforming source artifacts into cognitive representation bundles.

Directors coordinate.
Pipelines transform.
Contracts define.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .contracts import (
    ArtifactKind,
    RepresentationBundle,
)
from .segmentation import (
    DeterministicSemanticSegmenter,
    SEGMENTATION_VERSION,
    segment_text,
)


def _empty_metadata() -> Mapping[str, str]:
    """Return an immutable empty metadata mapping."""
    return MappingProxyType({})


def _freeze_metadata(metadata: Mapping[str, str]) -> Mapping[str, str]:
    """Return an immutable defensive copy of metadata."""
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True, slots=True)
class RepresentationRequest:
    """Canonical request accepted by the Representation Director."""

    artifact_id: str
    text: str
    artifact_kind: ArtifactKind = ArtifactKind.TEXT
    metadata: Mapping[str, str] = field(default_factory=_empty_metadata)

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, str):
            raise TypeError("artifact_id must be a string.")

        if not self.artifact_id.strip():
            raise ValueError("artifact_id cannot be empty.")

        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")

        if not isinstance(self.artifact_kind, ArtifactKind):
            raise TypeError("artifact_kind must be an ArtifactKind.")

        object.__setattr__(
            self,
            "metadata",
            _freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class RepresentationResult:
    """Canonical result returned by the Representation Director."""

    bundle: RepresentationBundle
    artifact_kind: ArtifactKind
    strategy_name: str
    strategy_version: str

    @property
    def source_id(self) -> str:
        """Return the represented source identifier."""
        return self.bundle.source_id

    @property
    def segment_count(self) -> int:
        """Return the number of structural segments produced."""
        return len(self.bundle.segments)


class UnsupportedArtifactKindError(ValueError):
    """Raised when no representation strategy supports an artifact kind."""


class RepresentationDirector:
    """Coordinate deterministic cognitive representation.

    Phase X-C2 initially routes supported textual artifacts through the
    stable X-C1 deterministic semantic segmenter. Future phases may add a
    registry and specialized pipelines without changing this public entry
    point.
    """

    _TEXTUAL_ARTIFACT_KINDS = frozenset(
        {
            ArtifactKind.TEXT,
            ArtifactKind.MARKDOWN,
            ArtifactKind.HTML,
            ArtifactKind.DOCUMENT,
            ArtifactKind.SOURCE_CODE,
        }
    )

    def __init__(
        self,
        *,
        segmenter: DeterministicSemanticSegmenter | None = None,
    ) -> None:
        self._segmenter = segmenter or DeterministicSemanticSegmenter()

    @property
    def supported_artifact_kinds(self) -> frozenset[ArtifactKind]:
        """Return artifact kinds supported by this Director."""
        return self._TEXTUAL_ARTIFACT_KINDS

    def supports(self, artifact_kind: ArtifactKind) -> bool:
        """Return whether the Director can represent an artifact kind."""
        return artifact_kind in self._TEXTUAL_ARTIFACT_KINDS

    def represent(
        self,
        request: RepresentationRequest,
    ) -> RepresentationResult:
        """Represent one artifact through the selected strategy."""
        if not isinstance(request, RepresentationRequest):
            raise TypeError(
                "request must be a RepresentationRequest instance."
            )

        if not self.supports(request.artifact_kind):
            raise UnsupportedArtifactKindError(
                "No representation strategy is registered for artifact "
                f"kind: {request.artifact_kind.value}"
            )

        segmentation_result = segment_text(
            artifact_id=request.artifact_id,
            text=request.text,
            artifact_kind=request.artifact_kind,
        )

        segments = tuple(
            self._attach_request_metadata(
                segment=segment,
                request=request,
            )
            for segment in segmentation_result.segments
        )

        bundle = RepresentationBundle(
            source_id=request.artifact_id,
            segments=segments,
        )

        return RepresentationResult(
            bundle=bundle,
            artifact_kind=request.artifact_kind,
            strategy_name="deterministic_semantic_segmentation",
            strategy_version=SEGMENTATION_VERSION,
        )

    @staticmethod
    def _attach_request_metadata(
        *,
        segment,
        request: RepresentationRequest,
    ):
        """Return a segment carrying request and strategy metadata.

        SemanticSegment is immutable, so a new instance is created while
        preserving the deterministic identifier, source span, and ordinal.
        """
        metadata = {
            **dict(segment.metadata),
            **dict(request.metadata),
            "representation_director": "phase_xc2",
            "representation_strategy": (
                "deterministic_semantic_segmentation"
            ),
        }

        return type(segment)(
            segment_id=segment.segment_id,
            artifact=segment.artifact,
            ordinal=segment.ordinal,
            kind=segment.kind,
            text=segment.text,
            span=segment.span,
            metadata=metadata,
        )


_DEFAULT_DIRECTOR = RepresentationDirector()


def represent_text(
    *,
    artifact_id: str,
    text: str,
    artifact_kind: ArtifactKind = ArtifactKind.TEXT,
    metadata: Mapping[str, str] | None = None,
) -> RepresentationResult:
    """Convenience entry point for deterministic representation."""
    request = RepresentationRequest(
        artifact_id=artifact_id,
        text=text,
        artifact_kind=artifact_kind,
        metadata={} if metadata is None else metadata,
    )
    return _DEFAULT_DIRECTOR.represent(request)
