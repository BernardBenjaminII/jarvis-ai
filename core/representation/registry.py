"""Deterministic representation pipeline registry.

Phase X-C2.2 introduces the registry used by the Representation Director
to discover representation pipelines without hardcoding pipeline
selection logic.

Directors coordinate.
Registries resolve.
Pipelines transform.
Contracts define.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Protocol, runtime_checkable

from .contracts import ArtifactKind


class RepresentationRegistryError(RuntimeError):
    """Base error for representation registry failures."""


class DuplicatePipelineRegistrationError(RepresentationRegistryError):
    """Raised when an artifact kind already has a registered pipeline."""


class PipelineNotRegisteredError(RepresentationRegistryError):
    """Raised when no pipeline is registered for an artifact kind."""


class InvalidPipelineRegistrationError(RepresentationRegistryError):
    """Raised when a pipeline registration is structurally invalid."""


@runtime_checkable
class RepresentationPipeline(Protocol):
    """Structural contract implemented by representation pipelines.

    A pipeline may support one or more artifact kinds. The pipeline's
    execution interface will be formalized in the pipeline phase; this
    registry intentionally depends only on stable identification and
    capability metadata.
    """

    @property
    def name(self) -> str:
        """Return the stable pipeline name."""

    @property
    def version(self) -> str:
        """Return the stable pipeline version."""

    @property
    def supported_artifact_kinds(self) -> frozenset[ArtifactKind]:
        """Return the artifact kinds supported by the pipeline."""


@dataclass(frozen=True, slots=True)
class PipelineRegistration:
    """Immutable description of one registered pipeline."""

    pipeline: RepresentationPipeline
    pipeline_name: str
    pipeline_version: str
    artifact_kinds: frozenset[ArtifactKind]

    def __post_init__(self) -> None:
        if not isinstance(self.pipeline_name, str):
            raise TypeError("pipeline_name must be a string.")

        if not self.pipeline_name.strip():
            raise ValueError("pipeline_name cannot be empty.")

        if not isinstance(self.pipeline_version, str):
            raise TypeError("pipeline_version must be a string.")

        if not self.pipeline_version.strip():
            raise ValueError("pipeline_version cannot be empty.")

        if not isinstance(self.artifact_kinds, frozenset):
            raise TypeError("artifact_kinds must be a frozenset.")

        if not self.artifact_kinds:
            raise ValueError(
                "A pipeline must support at least one artifact kind."
            )

        invalid_kinds = tuple(
            artifact_kind
            for artifact_kind in self.artifact_kinds
            if not isinstance(artifact_kind, ArtifactKind)
        )

        if invalid_kinds:
            raise TypeError(
                "artifact_kinds must contain only ArtifactKind values."
            )


class RepresentationRegistry:
    """Register and resolve representation pipelines deterministically."""

    def __init__(self) -> None:
        self._registrations_by_kind: dict[
            ArtifactKind,
            PipelineRegistration,
        ] = {}

        self._registrations_by_name: dict[
            str,
            PipelineRegistration,
        ] = {}

    @property
    def pipeline_count(self) -> int:
        """Return the number of uniquely registered pipelines."""
        return len(self._registrations_by_name)

    @property
    def artifact_kind_count(self) -> int:
        """Return the number of artifact kinds with registered pipelines."""
        return len(self._registrations_by_kind)

    @property
    def registered_pipeline_names(self) -> tuple[str, ...]:
        """Return registered pipeline names in deterministic order."""
        return tuple(sorted(self._registrations_by_name))

    @property
    def registered_artifact_kinds(self) -> tuple[ArtifactKind, ...]:
        """Return registered artifact kinds in deterministic value order."""
        return tuple(
            sorted(
                self._registrations_by_kind,
                key=lambda artifact_kind: artifact_kind.value,
            )
        )

    def register(
        self,
        pipeline: RepresentationPipeline,
    ) -> PipelineRegistration:
        """Register one pipeline for all artifact kinds it supports.

        Registration is atomic. If any artifact kind conflicts with an
        existing pipeline, no part of the new registration is retained.
        """
        registration = self._build_registration(pipeline)

        if registration.pipeline_name in self._registrations_by_name:
            existing = self._registrations_by_name[
                registration.pipeline_name
            ]

            raise DuplicatePipelineRegistrationError(
                "A representation pipeline named "
                f"{registration.pipeline_name!r} is already registered "
                f"at version {existing.pipeline_version!r}."
            )

        conflicts = tuple(
            artifact_kind
            for artifact_kind in registration.artifact_kinds
            if artifact_kind in self._registrations_by_kind
        )

        if conflicts:
            conflict_descriptions = ", ".join(
                (
                    f"{artifact_kind.value}="
                    f"{self._registrations_by_kind[artifact_kind].pipeline_name}"
                )
                for artifact_kind in sorted(
                    conflicts,
                    key=lambda item: item.value,
                )
            )

            raise DuplicatePipelineRegistrationError(
                "Representation pipeline registration conflicts with "
                f"existing artifact-kind assignments: "
                f"{conflict_descriptions}."
            )

        self._registrations_by_name[
            registration.pipeline_name
        ] = registration

        for artifact_kind in registration.artifact_kinds:
            self._registrations_by_kind[
                artifact_kind
            ] = registration

        return registration

    def unregister(
        self,
        pipeline_name: str,
    ) -> PipelineRegistration:
        """Remove one pipeline and all of its artifact-kind assignments."""
        normalized_name = self._normalize_pipeline_name(pipeline_name)

        try:
            registration = self._registrations_by_name.pop(
                normalized_name
            )
        except KeyError as exc:
            raise PipelineNotRegisteredError(
                "No representation pipeline is registered with the name "
                f"{normalized_name!r}."
            ) from exc

        for artifact_kind in registration.artifact_kinds:
            current = self._registrations_by_kind.get(artifact_kind)

            if current is registration:
                del self._registrations_by_kind[artifact_kind]

        return registration

    def resolve(
        self,
        artifact_kind: ArtifactKind,
    ) -> RepresentationPipeline:
        """Resolve the pipeline registered for an artifact kind."""
        return self.registration_for(artifact_kind).pipeline

    def registration_for(
        self,
        artifact_kind: ArtifactKind,
    ) -> PipelineRegistration:
        """Return registration metadata for an artifact kind."""
        self._validate_artifact_kind(artifact_kind)

        try:
            return self._registrations_by_kind[artifact_kind]
        except KeyError as exc:
            raise PipelineNotRegisteredError(
                "No representation pipeline is registered for artifact "
                f"kind {artifact_kind.value!r}."
            ) from exc

    def registration_named(
        self,
        pipeline_name: str,
    ) -> PipelineRegistration:
        """Return registration metadata for a pipeline name."""
        normalized_name = self._normalize_pipeline_name(pipeline_name)

        try:
            return self._registrations_by_name[normalized_name]
        except KeyError as exc:
            raise PipelineNotRegisteredError(
                "No representation pipeline is registered with the name "
                f"{normalized_name!r}."
            ) from exc

    def supports(
        self,
        artifact_kind: ArtifactKind,
    ) -> bool:
        """Return whether an artifact kind has a registered pipeline."""
        self._validate_artifact_kind(artifact_kind)
        return artifact_kind in self._registrations_by_kind

    def snapshot(
        self,
    ) -> Mapping[ArtifactKind, PipelineRegistration]:
        """Return an immutable defensive registry snapshot."""
        ordered_snapshot = {
            artifact_kind: self._registrations_by_kind[artifact_kind]
            for artifact_kind in self.registered_artifact_kinds
        }

        return MappingProxyType(ordered_snapshot)

    def clear(self) -> None:
        """Remove all pipeline registrations."""
        self._registrations_by_kind.clear()
        self._registrations_by_name.clear()

    @staticmethod
    def _build_registration(
        pipeline: RepresentationPipeline,
    ) -> PipelineRegistration:
        """Validate a pipeline and create its immutable registration."""
        if pipeline is None:
            raise InvalidPipelineRegistrationError(
                "pipeline cannot be None."
            )

        try:
            pipeline_name = pipeline.name
            pipeline_version = pipeline.version
            supported_kinds = pipeline.supported_artifact_kinds
        except AttributeError as exc:
            raise InvalidPipelineRegistrationError(
                "A representation pipeline must expose name, version, "
                "and supported_artifact_kinds."
            ) from exc

        if not isinstance(pipeline_name, str):
            raise InvalidPipelineRegistrationError(
                "pipeline.name must be a string."
            )

        normalized_name = pipeline_name.strip()

        if not normalized_name:
            raise InvalidPipelineRegistrationError(
                "pipeline.name cannot be empty."
            )

        if not isinstance(pipeline_version, str):
            raise InvalidPipelineRegistrationError(
                "pipeline.version must be a string."
            )

        normalized_version = pipeline_version.strip()

        if not normalized_version:
            raise InvalidPipelineRegistrationError(
                "pipeline.version cannot be empty."
            )

        artifact_kinds = RepresentationRegistry._normalize_artifact_kinds(
            supported_kinds
        )

        return PipelineRegistration(
            pipeline=pipeline,
            pipeline_name=normalized_name,
            pipeline_version=normalized_version,
            artifact_kinds=artifact_kinds,
        )

    @staticmethod
    def _normalize_artifact_kinds(
        artifact_kinds: Iterable[ArtifactKind],
    ) -> frozenset[ArtifactKind]:
        """Validate and freeze a pipeline's supported artifact kinds."""
        if isinstance(artifact_kinds, (str, bytes)):
            raise InvalidPipelineRegistrationError(
                "supported_artifact_kinds must be an iterable of "
                "ArtifactKind values."
            )

        try:
            normalized = frozenset(artifact_kinds)
        except TypeError as exc:
            raise InvalidPipelineRegistrationError(
                "supported_artifact_kinds must be iterable."
            ) from exc

        if not normalized:
            raise InvalidPipelineRegistrationError(
                "A pipeline must support at least one artifact kind."
            )

        invalid_kinds = tuple(
            artifact_kind
            for artifact_kind in normalized
            if not isinstance(artifact_kind, ArtifactKind)
        )

        if invalid_kinds:
            raise InvalidPipelineRegistrationError(
                "supported_artifact_kinds must contain only "
                "ArtifactKind values."
            )

        return normalized

    @staticmethod
    def _validate_artifact_kind(
        artifact_kind: ArtifactKind,
    ) -> None:
        """Validate an artifact-kind lookup argument."""
        if not isinstance(artifact_kind, ArtifactKind):
            raise TypeError(
                "artifact_kind must be an ArtifactKind instance."
            )

    @staticmethod
    def _normalize_pipeline_name(
        pipeline_name: str,
    ) -> str:
        """Validate and normalize a pipeline-name lookup argument."""
        if not isinstance(pipeline_name, str):
            raise TypeError("pipeline_name must be a string.")

        normalized_name = pipeline_name.strip()

        if not normalized_name:
            raise ValueError("pipeline_name cannot be empty.")

        return normalized_name
